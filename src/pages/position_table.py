"""Shared position-table presentation and status-editing helpers."""

from __future__ import annotations

import dash_ag_grid as dag
from dash import html

from ..storage import get_players_for_position_grid, set_player_drafted

POSITION_NAMES = {"F": "Forwards", "D": "Defencemen", "G": "Goalies"}


def position_grid_id(position: str) -> str:
    """Return the stable component id for a position's player grid."""
    return f"{position.lower()}-player-grid"


def get_position_rows(position: str) -> list[dict]:
    """Return the current persisted player rows for one position."""
    return get_players_for_position_grid(position).to_dict("records")


def handle_drafted_cell_change(position: str, cell_change: dict | None) -> list[dict]:
    """Persist a drafted checkbox edit and return fresh rows for the grid."""
    if not cell_change or cell_change.get("colId") != "drafted":
        return get_position_rows(position)

    row_data = cell_change.get("data") or {}
    player_id = row_data.get("id")
    drafted = cell_change.get("newValue")
    if not isinstance(player_id, int) or not isinstance(drafted, bool):
        raise ValueError("Drafted status updates require an integer player id and a boolean value.")

    set_player_drafted(player_id, drafted)
    return get_position_rows(position)


def build_position_layout(position: str):
    """Build a dedicated live-draft table for one player position."""
    title = POSITION_NAMES[position]
    return html.Div(
        style={"maxWidth": "760px"},
        children=[
            html.H2(title),
            html.P("Check Status when a player has been drafted. Drafted players remain visible but are grayed out."),
            dag.AgGrid(
                id=position_grid_id(position),
                rowData=get_position_rows(position),
                columnDefs=[
                    {"field": "name", "headerName": "Name"},
                    {
                        "field": "drafted",
                        "headerName": "Status",
                        "editable": True,
                        "cellRenderer": "agCheckboxCellRenderer",
                        "cellEditor": "agCheckboxCellEditor",
                    },
                ],
                defaultColDef={"sortable": True, "resizable": True},
                dashGridOptions={
                    "getRowStyle": {
                        "function": "params.data.drafted ? {color: '#888', backgroundColor: '#f2f2f2'} : null"
                    }
                },
                style={"height": "640px", "width": "100%"},
            ),
        ],
    )
