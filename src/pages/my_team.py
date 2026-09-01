"""My Team page: drafted players explicitly assigned to the user's team."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, html

from .position_table import build_position_grid, handle_player_cell_change

PATH = "/my-team"
NAME = "My Team"
ORDER = 4
POSITIONS = ("F", "D", "G")


def grid_id(position: str) -> str:
    """Return a My Team grid id for a position."""
    return f"my-team-{position.lower()}-player-grid"


def layout(**_kwargs):
    """Build separate position tables from the persisted My Team subset."""
    return html.Div(
        className="my-team-page",
        children=[
            html.H2("My Team"),
            *[
                html.Section(
                    className="my-team-position",
                    children=[html.H3({"F": "Forwards", "D": "Defencemen", "G": "Goalies"}[position]),
                              build_position_grid(position, my_team_only=True)],
                )
                for position in POSITIONS
            ],
        ],
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


for _position in POSITIONS:
    @callback(
        Output(grid_id(_position), "rowData"),
        Input(grid_id(_position), "cellValueChanged"),
        prevent_initial_call=True,
    )
    def update_my_team_player(cell_changes, position=_position):
        return handle_player_cell_change(position, cell_changes, my_team_only=True)
