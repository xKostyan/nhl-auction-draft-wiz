"""Page 1 - live draft table for forwards."""

from __future__ import annotations

import dash
from dash import Input, Output, callback

from .position_table import (
    build_position_layout,
    handle_player_context_action,
    get_player_search_target,
    handle_drafted_cell_change,
    position_grid_id,
    position_search_id,
)

PATH = "/forwards"
NAME = "Forwards"
ORDER = 1
POSITION = "F"
GRID_ID = position_grid_id(POSITION)
SEARCH_ID = position_search_id(POSITION)


def layout(**_kwargs):
    """Build the forwards table from current workspace state."""
    return build_position_layout(POSITION)


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


@callback(
    Output(GRID_ID, "rowData"),
    Input(GRID_ID, "cellValueChanged"),
    Input(GRID_ID, "cellRendererData"),
    prevent_initial_call=True,
)
def update_drafted_status(cell_change, context_action):
    if context_action:
        return handle_player_context_action(POSITION, context_action)
    return handle_drafted_cell_change(POSITION, cell_change)


@callback(
    Output(GRID_ID, "selectedRows"),
    Output(GRID_ID, "scrollTo"),
    Input(SEARCH_ID, "value"),
)
def focus_searched_player(player_id):
    return get_player_search_target(POSITION, player_id)
