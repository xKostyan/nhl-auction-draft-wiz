"""My Team page: drafted players explicitly assigned to the user's team."""

from __future__ import annotations

import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html

from .position_table import (
    build_my_team_snapshot,
    build_my_team_grid,
    get_my_team_goalie_projection,
    get_my_team_table_heading,
    get_my_team_table_rows,
    get_workspace_value,
    persist_my_team_grid_update,
)
from ..storage import get_draft_budget, set_draft_budget, set_workspace_value

PATH = "/my-team"
NAME = "My Team"
ORDER = 4
TABLES = ("F", "D", "utility", "G", "bench")
CHART_ID = "my-team-projection-chart"
BUDGET_INPUT_ID = "draft-budget"
BUDGET_SUMMARY_ID = "budget-summary"
BUDGET_STATUS_ID = "budget-status"
SKATER_ALLOCATION_ID = "budget-skater-percent"
GOALIE_ALLOCATION_ID = "budget-goalie-percent"
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
        height=460,
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


def _budget_int(value: object, label: str) -> int:
    """Parse a non-negative whole-number budget setting from Dash input data."""
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a non-negative whole number.")
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, float) and value.is_integer() and value >= 0:
        return int(value)
    if isinstance(value, str) and value.strip().isdecimal():
        return int(value.strip())
    raise ValueError(f"{label} must be a non-negative whole number.")


def _player_price(value: object) -> int:
    """Treat legacy blank roster prices as zero while validating populated prices."""
    return 0 if value is None else _budget_int(value, "Player price")


def _stored_percentage(key: str, default: int) -> int:
    """Read a stored allocation percentage, falling back for legacy workspaces."""
    value = get_workspace_value(key)
    return int(value) if value.isdecimal() else default


def get_budget_summary(
    *, snapshot: dict[str, list[dict]] | None = None, budget: int | None = None
) -> dict[str, int | float]:
    """Calculate the global auction constraints from roster prices and empty slots."""
    if snapshot is None:
        snapshot = build_my_team_snapshot()
    total_budget = get_draft_budget() if budget is None else _budget_int(budget, "Draft budget")
    roster_rows = [
        row for table_rows in snapshot.values() for row in table_rows if not row.get("is_empty_slot")
    ]
    committed = sum(_player_price(row["price"]) for row in roster_rows)
    empty_slots = sum(
        1 for table_rows in snapshot.values() for row in table_rows if row.get("is_empty_slot")
    )
    available = total_budget - committed
    reserved_minimums = empty_slots
    flexible = max(0, available - reserved_minimums)
    return {
        "total_budget": total_budget,
        "committed": committed,
        "empty_slots": empty_slots,
        "reserved_minimums": reserved_minimums,
        "available": available,
        "flexible": flexible,
        "max_next_bid": max(0, available - max(0, empty_slots - 1)),
    }


def get_budget_allocation(
    percentages: dict[str, object],
    *,
    snapshot: dict[str, list[dict]] | None = None,
    budget: int | None = None,
) -> list[dict[str, int | float | str]]:
    """Return advisory Skaters/Goalies allocations; the maximum bid remains authoritative."""
    summary = get_budget_summary(snapshot=snapshot, budget=budget)
    groups = (("Skaters", {"F", "D"}, "skaters"), ("Goalies", {"G"}, "goalies"))
    percentage_total = sum(_budget_int(percentages[key], f"{label} allocation") for label, _, key in groups)
    if percentage_total != 100:
        raise ValueError("Budget allocation percentages must total 100.")

    roster_rows = [
        row for table_rows in (snapshot or build_my_team_snapshot()).values()
        for row in table_rows if not row.get("is_empty_slot")
    ]
    open_primary_slots = {
        "F": sum(row.get("is_empty_slot", False) for row in (snapshot or build_my_team_snapshot())["F"]),
        "D": sum(row.get("is_empty_slot", False) for row in (snapshot or build_my_team_snapshot())["D"]),
        "G": sum(row.get("is_empty_slot", False) for row in (snapshot or build_my_team_snapshot())["G"]),
    }
    rows = []
    for label, positions, key in groups:
        planned = summary["total_budget"] * _budget_int(percentages[key], f"{label} allocation") / 100
        committed = sum(
            _player_price(row["price"])
            for row in roster_rows if row["position"] in positions
        )
        open_slots = sum(open_primary_slots[position] for position in positions)
        minimum_reserve = open_slots
        remaining = planned - committed - minimum_reserve
        rows.append({
            "label": label,
            "planned": planned,
            "committed": committed,
            "open_slots": open_slots,
            "minimum_reserve": minimum_reserve,
            "remaining": remaining,
            "average": max(0, remaining) / open_slots if open_slots else 0,
        })
    return rows


def build_budget_summary(
    percentages: dict[str, object] | None = None,
    *,
    snapshot: dict[str, list[dict]] | None = None,
) -> html.Div:
    """Build live global and advisory budget information for the My Team page."""
    summary = get_budget_summary(snapshot=snapshot)
    percentages = percentages or {
        "skaters": 80,
        "goalies": 20,
    }
    allocation_rows = get_budget_allocation(percentages, snapshot=snapshot)
    metrics = [
        ("Committed", summary["committed"]),
        ("Available", summary["available"]),
        ("Reserved at $1", summary["reserved_minimums"]),
        ("Max next bid", summary["max_next_bid"]),
    ]
    return html.Div([
        html.Div(
            [
                html.Div(
                    [
                        html.Span(label, className="budget-metric-label"),
                        html.Strong(f"${value:,.0f}"),
                    ],
                    className="budget-metric",
                )
                for label, value in metrics
            ],
            className="budget-metrics",
        ),
        html.P(
            f"{summary['empty_slots']} open slots; flexible budget: ${summary['flexible']:,.0f}",
            className="budget-explanation",
        ),
        html.Table(
            [
                html.Thead(html.Tr([html.Th(name) for name in (
                    "Allocation", "Planned", "Spent", "Minimum", "Remaining", "Avg / slot"
                )])),
                html.Tbody([
                    html.Tr([html.Td(value) for value in (
                        row["label"], f"${row['planned']:,.0f}", f"${row['committed']:,.0f}",
                        f"${row['minimum_reserve']:,.0f}",
                        f"${row['remaining']:,.0f}", f"${row['average']:,.2f}",
                    )])
                    for row in allocation_rows
                ]),
            ],
            className="budget-allocation-table",
        ),
    ])


def build_budget_update(
    budget: object,
    skater_percentage: object,
    goalie_percentage: object,
) -> tuple[list, str]:
    """Persist valid budget settings and return refreshed budget-panel outputs."""
    percentages = {
        "skaters": skater_percentage,
        "goalies": goalie_percentage,
    }
    try:
        parsed_budget = _budget_int(budget, "Draft budget")
        get_budget_allocation(percentages, budget=parsed_budget)
        set_draft_budget(parsed_budget)
        set_workspace_value("budget_skater_percent", str(_budget_int(skater_percentage, "Skaters allocation")))
        set_workspace_value("budget_goalie_percent", str(_budget_int(goalie_percentage, "Goalies allocation")))
        return build_budget_summary(percentages).children, ""
    except ValueError as error:
        return build_budget_summary().children, str(error)


def _budget_controls(*, snapshot: dict[str, list[dict]]) -> html.Section:
    """Build the persistent budget inputs and their initial allocation view."""
    skater_percentage = _stored_percentage("budget_skater_percent", 80)
    goalie_percentage = _stored_percentage("budget_goalie_percent", 20)
    percentages = {
        "skaters": skater_percentage,
        "goalies": goalie_percentage,
    }
    return html.Section(
        className="budget-panel",
        children=[
            html.H4("Draft budget"),
            html.Label(["Total budget", dcc.Input(
                id=BUDGET_INPUT_ID, type="number", min=0, step=1, value=get_draft_budget()
            )]),
            html.Div([
                html.Label(["Skaters %", dcc.Input(id=SKATER_ALLOCATION_ID, type="number", min=0, max=100, step=1, value=skater_percentage)]),
                html.Label(["Goalies %", dcc.Input(id=GOALIE_ALLOCATION_ID, type="number", min=0, max=100, step=1, value=goalie_percentage)]),
            ]),
            html.Div(id=BUDGET_STATUS_ID, role="status"),
            html.Div(id=BUDGET_SUMMARY_ID, children=build_budget_summary(percentages, snapshot=snapshot)),
        ],
    )


def build_my_team_table_heading(
    table: str, *, snapshot: dict[str, list[dict]] | None = None
) -> html.H3:
    """Build a consistently aligned My Team table heading."""
    title, projection_label, projected_total = get_my_team_table_heading(
        table, snapshot=snapshot
    )
    return html.H3(
        [
            html.Span(title, className="my-team-heading-title"),
            html.Span(projection_label, className="my-team-heading-projection"),
            html.Span(projected_total, className="my-team-heading-total"),
        ],
        id=title_id(table),
        className="my-team-table-heading",
    )


def layout(**_kwargs):
    """Build separate position tables from the persisted My Team subset."""
    snapshot = build_my_team_snapshot()
    return html.Div(
        className="my-team-page",
        children=[
            html.H2("My Team"),
            html.Div(
                className="my-team-overview",
                children=[
                    _budget_controls(snapshot=snapshot),
                    dcc.Graph(
                        id=CHART_ID,
                        figure=build_projection_chart(snapshot=snapshot),
                        config={"displayModeBar": False},
                    ),
                ],
            ),
            *[
                html.Section(
                    className="my-team-position",
                    children=[
                        build_my_team_table_heading(table, snapshot=snapshot),
                        build_my_team_grid(table, snapshot=snapshot),
                    ],
                )
                for table in TABLES
            ],
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
    return _build_my_team_outputs(snapshot)


def _build_my_team_outputs(snapshot: dict[str, list[dict]]) -> tuple[list[dict], ...]:
    """Build the shared grid, heading, and chart outputs from one roster snapshot."""
    return (
        *(snapshot[current_table] for current_table in TABLES),
        *(
            build_my_team_table_heading(current_table, snapshot=snapshot).children
            for current_table in TABLES
        ),
        build_projection_chart(snapshot=snapshot),
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


@callback(
    *(Output(grid_id(table), "rowData") for table in TABLES),
    *(Output(title_id(table), "children") for table in TABLES),
    Output(CHART_ID, "figure"),
    Output(BUDGET_SUMMARY_ID, "children"),
    Output(BUDGET_STATUS_ID, "children"),
    Input(BUDGET_INPUT_ID, "value"),
    Input(SKATER_ALLOCATION_ID, "value"),
    Input(GOALIE_ALLOCATION_ID, "value"),
    *(Input(grid_id(table), "cellValueChanged") for table in TABLES),
    *(Input(grid_id(table), "cellRendererData") for table in TABLES),
    prevent_initial_call=True,
)
def update_my_team_player(*values):
    """Refresh every placement-dependent roster view after a My Team edit."""
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, str):
        raise ValueError("My Team grid updates require a triggered grid id.")
    budget_values = values[:3]
    table = next(
        (
            current_table
            for current_table in TABLES
            if triggered_id == grid_id(current_table)
        ),
        None,
    )
    budget_update = build_budget_update(*budget_values)
    if table is None and triggered_id in {BUDGET_INPUT_ID, SKATER_ALLOCATION_ID, GOALIE_ALLOCATION_ID}:
        return (*_build_my_team_outputs(build_my_team_snapshot()), *budget_update)
    if table is None:
        raise ValueError(f"Unsupported My Team grid id: {triggered_id!r}.")

    table_index = TABLES.index(table)
    cell_changes = values[3 + table_index]
    context_action = values[3 + len(TABLES) + table_index]
    triggered_property = ctx.triggered[0]["prop_id"].rsplit(".", 1)[-1]
    return (*build_my_team_update(table, cell_changes, context_action, triggered_property), *budget_update)
