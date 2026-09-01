"""My Team page: drafted players explicitly assigned to the user's team."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, ctx, html

from .position_table import MY_TEAM_TABLES, build_my_team_grid, handle_my_team_grid_update

PATH = "/my-team"
NAME = "My Team"
ORDER = 4
TABLES = ("F", "D", "utility", "G", "bench")


def grid_id(table: str) -> str:
    """Return a My Team grid id for a roster table."""
    return f"my-team-{table.lower()}-player-grid"


def layout(**_kwargs):
    """Build separate position tables from the persisted My Team subset."""
    return html.Div(
        className="my-team-page",
        children=[
            html.H2("My Team"),
            *[
                html.Section(
                    className="my-team-position",
                    children=[html.H3(MY_TEAM_TABLES[table]["title"]), build_my_team_grid(table)],
                )
                for table in TABLES
            ],
        ],
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


for _table in TABLES:
    @callback(
        Output(grid_id(_table), "rowData"),
        Input(grid_id(_table), "cellValueChanged"),
        Input(grid_id(_table), "cellRendererData"),
        prevent_initial_call=True,
    )
    def update_my_team_player(cell_changes, context_action, table=_table):
        return handle_my_team_grid_update(
            table,
            cell_changes,
            context_action,
            ctx.triggered[0]["prop_id"].rsplit(".", 1)[-1],
        )
