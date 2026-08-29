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


def _parse_player_id(value: object) -> int:
    """Convert the JSON-compatible grid row id to a database player id."""
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)
    raise ValueError("Drafted status updates require a positive integer player id.")


def _parse_drafted_value(value: object) -> bool:
    """Convert the JSON-compatible checkbox value to a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ValueError("Drafted status updates require a boolean checkbox value.")


def handle_drafted_cell_change(position: str, cell_changes: list[dict] | None) -> list[dict]:
    """Persist the most recent drafted checkbox edit and return fresh grid rows.

    Dash AG Grid provides ``cellValueChanged`` as a list of event dictionaries,
    even when exactly one cell was changed.
    """
    if not cell_changes:
        return get_position_rows(position)

    cell_change = cell_changes[-1]
    if not isinstance(cell_change, dict):
        raise ValueError("Drafted status updates require an AG Grid event dictionary.")
    if cell_change.get("colId") != "drafted":
        return get_position_rows(position)

    row_data = cell_change.get("data") or {}
    if not isinstance(row_data, dict):
        raise ValueError("Drafted status updates require AG Grid row data.")

    player_id = _parse_player_id(row_data.get("id"))
    drafted = _parse_drafted_value(cell_change.get("newValue"))

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
