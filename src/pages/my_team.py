"""My Team page: drafted players explicitly assigned to the user's team."""

from __future__ import annotations

import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html

from .position_table import (
    build_my_team_grid,
    get_my_team_goalie_projection,
    get_my_team_table_title,
    get_my_team_table_rows,
    get_workspace_value,
    handle_my_team_grid_update,
)

PATH = "/my-team"
NAME = "My Team"
ORDER = 4
TABLES = ("F", "D", "utility", "G", "bench")
CHART_ID = "my-team-projection-chart"
_GROUPS = (("F", "Forwards"), ("D", "Defencemen"), ("utility", "Utility"), ("G", "Goalies"))
_GROUP_COLORS = {"F": "#1f77b4", "D": "#ff7f0e", "utility": "#2ca02c", "G": "#9467bd"}


def grid_id(table: str) -> str:
    """Return a My Team grid id for a roster table."""
    return f"my-team-{table.lower()}-player-grid"


def title_id(table: str) -> str:
    """Return a My Team table title id."""
    return f"my-team-{table.lower()}-title"


def build_projection_chart() -> go.Figure:
    """Build the two-layer projected-points donut for the active roster."""
    group_values = []
    outer_labels = []
    outer_values = []
    outer_colors = []
    for table, label in _GROUPS:
        if table == "G":
            value = get_my_team_goalie_projection()["projected_points"]
            players = _goalie_chart_players()
        else:
            players = [
                (row["name"], _number(row.get("projected_tfp")))
                for row in get_my_team_table_rows(table)
                if not row.get("is_empty_slot")
            ]
            value = sum(player_value for _, player_value in players)
        group_values.append(value)
        outer_labels.extend(f"{label}: {name}" for name, _ in players)
        outer_values.extend(player_value for _, player_value in players)
        outer_colors.extend([_GROUP_COLORS[table]] * len(players))

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
                domain={"x": [0, 1], "y": [0, 1]},
            ),
            go.Pie(
                labels=outer_labels,
                values=outer_values,
                hole=0.72,
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
        height=460,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        showlegend=False,
    )
    return figure


def _goalie_chart_players() -> list[tuple[str, float]]:
    """Return goalie contributions using the same priority and 140-start cap."""
    candidates = [
        row for row in get_my_team_table_rows("G") if not row.get("is_empty_slot")
    ] + sorted(
        [
            row for row in get_my_team_table_rows("bench")
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
    return html.Div(
        className="my-team-page",
        children=[
            html.H2("My Team"),
            dcc.Graph(id=CHART_ID, figure=build_projection_chart(), config={"displayModeBar": False}),
            *[
                html.Section(
                    className="my-team-position",
                    children=[html.H3(get_my_team_table_title(table), id=title_id(table)), build_my_team_grid(table)],
                )
                for table in TABLES
            ],
        ],
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


for _table in TABLES:
    @callback(
        Output(grid_id(_table), "rowData"),
        Output(title_id(_table), "children"),
        Output(CHART_ID, "figure", allow_duplicate=True),
        Input(grid_id(_table), "cellValueChanged"),
        Input(grid_id(_table), "cellRendererData"),
        prevent_initial_call=True,
    )
    def update_my_team_player(cell_changes, context_action, table=_table):
        rows = handle_my_team_grid_update(
            table,
            cell_changes,
            context_action,
            ctx.triggered[0]["prop_id"].rsplit(".", 1)[-1],
        )
        return rows, get_my_team_table_title(table), build_projection_chart()
