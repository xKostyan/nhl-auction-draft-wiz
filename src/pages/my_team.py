"""My Team page: drafted players explicitly assigned to the user's team."""

from __future__ import annotations

import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html

from .position_table import (
    build_my_team_snapshot,
    build_my_team_grid,
    get_my_team_goalie_projection,
    get_my_team_table_title,
    get_my_team_table_rows,
    get_workspace_value,
    persist_my_team_grid_update,
)

PATH = "/my-team"
NAME = "My Team"
ORDER = 4
TABLES = ("F", "D", "utility", "G", "bench")
CHART_ID = "my-team-projection-chart"
_GROUPS = (("F", "Forwards"), ("D", "Defencemen"), ("utility", "Utility"), ("G", "Goalies"))
_GROUP_COLORS = {"F": "#ff8533", "D": "#5cd65c", "utility": "#33adff", "G": "#cc33ff"}
_PLAYER_COLORS = {
    "F": ("#ff8533", "#ff9d5c", "#e66f1f", "#ffb380", "#cc5f17", "#ffd0b3", "#f57c00", "#ffab73", "#b84f12"),
    "D": ("#5cd65c", "#83e683", "#3fbf3f", "#a3efa3", "#2e9c2e", "#c2f5c2", "#48c948", "#76dc76"),
    "utility": ("#33adff", "#66c2ff", "#1688d9", "#99d6ff", "#0f6fae", "#b3e3ff"),
    "G": ("#cc33ff", "#dc70ff", "#ad1fd6", "#e7a3ff", "#8610aa", "#f0c2ff"),
}


def grid_id(table: str) -> str:
    """Return a My Team grid id for a roster table."""
    return f"my-team-{table.lower()}-player-grid"


def title_id(table: str) -> str:
    """Return a My Team table title id."""
    return f"my-team-{table.lower()}-title"


def build_projection_chart(*, snapshot: dict[str, list[dict]] | None = None) -> go.Figure:
    """Build the two-layer projected-points donut for the active roster."""
    group_values = []
    outer_labels = []
    outer_values = []
    outer_colors = []
    for table, label in _GROUPS:
        if table == "G":
            value = get_my_team_goalie_projection(snapshot=snapshot)["projected_points"]
            players = _goalie_chart_players(snapshot=snapshot)
        else:
            players = [
                (row["name"], _number(row.get("projected_tfp")))
                for row in get_my_team_table_rows(table, snapshot=snapshot)
                if not row.get("is_empty_slot")
            ]
            value = sum(player_value for _, player_value in players)
        group_values.append(value)
        outer_labels.extend(f"{label}: {name}" for name, _ in players)
        outer_values.extend(player_value for _, player_value in players)
        outer_colors.extend(_player_color(table, index) for index in range(len(players)))

    grand_total = sum(group_values)
    figure = go.Figure(
        data=[
            go.Pie(
                labels=[label for _, label in _GROUPS],
                values=group_values,
                hole=0.48,
                sort=False,
                direction="clockwise",
                marker={"colors": [_GROUP_COLORS[table] for table, _ in _GROUPS]},
                textinfo="label+percent",
                domain={"x": [0.1, 0.9], "y": [0.1, 0.9]},
            ),
            go.Pie(
                labels=outer_labels,
                values=outer_values,
                hole=0.84,
                sort=False,
                direction="clockwise",
                marker={"colors": outer_colors},
                textinfo="none",
                hovertemplate="%{label}<br>p TFP: %{value:.2f}<extra></extra>",
                domain={"x": [0, 1], "y": [0, 1]},
            ),
        ]
    )
    figure.update_layout(
        annotations=[{"text": f"Projected TFP<br><b>{grand_total:.2f}</b>", "showarrow": False, "font": {"size": 18}}],
        height=300,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        showlegend=False,
    )
    return figure


def _player_color(table: str, index: int) -> str:
    """Return a distinct player shade within the table's position color family."""
    return _PLAYER_COLORS[table][index % len(_PLAYER_COLORS[table])]


def _goalie_chart_players(
    *, snapshot: dict[str, list[dict]] | None = None
) -> list[tuple[str, float]]:
    """Return goalie contributions using the same priority and 140-start cap."""
    candidates = [
        row
        for row in get_my_team_table_rows("G", snapshot=snapshot)
        if not row.get("is_empty_slot")
    ] + sorted(
        [
            row for row in get_my_team_table_rows("bench", snapshot=snapshot)
            if not row.get("is_empty_slot") and row.get("position") == "G"
        ],
        key=lambda row: _number(row.get("projected_afp")),
        reverse=True,
    )
    remaining_starts = 140.0
    current_season = get_workspace_value("current_season")
    players = []
    for goalie in candidates:
        starts = 0.0
        for season in goalie.get("game_starts_history", []):
            if str(season.get("year")) == current_season:
                starts = _number(season.get("projected"))
                break
        counted_starts = min(0.9 * starts, remaining_starts)
        players.append((goalie["name"], counted_starts * _number(goalie.get("projected_afp"))))
        remaining_starts -= counted_starts
        if remaining_starts <= 0:
            break
    return players


def _number(value: object) -> float:
    """Normalize missing projected values for chart display."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return value if value == value else 0.0


def layout(**_kwargs):
    """Build separate position tables from the persisted My Team subset."""
    snapshot = build_my_team_snapshot()
    return html.Div(
        className="my-team-page",
        children=[
            html.H2("My Team"),
            *[
                html.Section(
                    className="my-team-position",
                    children=[
                        html.H3(
                            get_my_team_table_title(table, snapshot=snapshot),
                            id=title_id(table),
                        ),
                        build_my_team_grid(table, snapshot=snapshot),
                    ],
                )
                for table in TABLES
                if table != "bench"
            ],
            html.Div(
                className="my-team-bench-and-chart",
                children=[
                    html.Section(
                        className="my-team-position",
                        children=[
                            html.H3(
                                get_my_team_table_title("bench", snapshot=snapshot),
                                id=title_id("bench"),
                            ),
                            build_my_team_grid("bench", snapshot=snapshot),
                        ],
                    ),
                    dcc.Graph(
                        id=CHART_ID,
                        className="my-team-projection-chart",
                        figure=build_projection_chart(snapshot=snapshot),
                        config={"displayModeBar": False},
                    ),
                ],
            ),
        ],
    )


def build_my_team_update(
    table: str,
    cell_changes: list[dict] | None,
    context_action: dict | None,
    triggered_property: str,
) -> tuple[list[dict], ...]:
    """Persist an event and return one consistent update for every roster view."""
    persist_my_team_grid_update(table, cell_changes, context_action, triggered_property)
    snapshot = build_my_team_snapshot()
    return (
        *(snapshot[current_table] for current_table in TABLES),
        *(get_my_team_table_title(current_table, snapshot=snapshot) for current_table in TABLES),
        build_projection_chart(snapshot=snapshot),
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


@callback(
    *(Output(grid_id(table), "rowData") for table in TABLES),
    *(Output(title_id(table), "children") for table in TABLES),
    Output(CHART_ID, "figure"),
    *(Input(grid_id(table), "cellValueChanged") for table in TABLES),
    *(Input(grid_id(table), "cellRendererData") for table in TABLES),
    prevent_initial_call=True,
)
def update_my_team_player(*values):
    """Refresh every placement-dependent roster view after a My Team edit."""
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, str):
        raise ValueError("My Team grid updates require a triggered grid id.")
    table = next(
        (
            current_table
            for current_table in TABLES
            if triggered_id == grid_id(current_table)
        ),
        None,
    )
    if table is None:
        raise ValueError(f"Unsupported My Team grid id: {triggered_id!r}.")

    table_index = TABLES.index(table)
    cell_changes = values[table_index]
    context_action = values[len(TABLES) + table_index]
    triggered_property = ctx.triggered[0]["prop_id"].rsplit(".", 1)[-1]
    return build_my_team_update(table, cell_changes, context_action, triggered_property)
