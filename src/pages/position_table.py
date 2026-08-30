"""Shared position-table presentation and status-editing helpers."""

from __future__ import annotations

import dash_ag_grid as dag
from dash import html

from ..storage import (
    get_players_for_position_grid,
    get_workspace_value,
    set_player_drafted,
)

POSITION_NAMES = {"F": "Forwards", "D": "Defencemen", "G": "Goalies"}
SKATER_POSITIONS = {"F", "D"}


def position_grid_id(position: str) -> str:
    """Return the stable component id for a position's player grid."""
    return f"{position.lower()}-player-grid"


def get_position_rows(position: str) -> list[dict]:
    """Return the current persisted player rows for one position."""
    return get_players_for_position_grid(position).to_dict("records")


def _projected_points_column_defs() -> list[dict]:
    """Return projected fantasy-point columns labeled for the draft season."""
    current_season = get_workspace_value("current_season")
    year_label = current_season if current_season and current_season != "0" else "upcoming"
    return [
        {
            "field": "projected_tfp",
            "headerName": f"p TFP {year_label}",
            "type": "numericColumn",
        },
        {
            "field": "projected_afp",
            "headerName": f"p AFP {year_label}",
            "type": "numericColumn",
        },
    ]


def _health_column_def(position: str) -> list[dict]:
    """Return the actual-GP health sparkline column for skater tables."""
    if position not in SKATER_POSITIONS:
        return []
    return [
        {
            "field": "actual_gp_history",
            "headerName": "Health (actual GP)",
            "cellRenderer": "actualGpSparkline",
            "sortable": False,
            "resizable": False,
            "width": 132,
        }
    ]


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
    """Persist drafted checkbox edits and return fresh grid rows.

    Dash AG Grid provides ``cellValueChanged`` as a list of event dictionaries,
    even when exactly one cell was changed. Process every event because a
    clipboard action can update multiple status cells in one callback.
    """
    if not cell_changes:
        return get_position_rows(position)

    for cell_change in cell_changes:
        if not isinstance(cell_change, dict):
            raise ValueError("Drafted status updates require an AG Grid event dictionary.")
        if cell_change.get("colId") != "drafted":
            continue

        row_data = cell_change.get("data") or {}
        if not isinstance(row_data, dict):
            raise ValueError("Drafted status updates require AG Grid row data.")

        player_id = _parse_player_id(row_data.get("id"))
        drafted_value = cell_change.get("newValue")
        if drafted_value is None:
            drafted_value = cell_change.get("value")
        drafted = _parse_drafted_value(drafted_value)

        set_player_drafted(player_id, drafted)
    return get_position_rows(position)


def build_position_layout(position: str):
    """Build a dedicated live-draft table for one player position."""
    title = POSITION_NAMES[position]
    return html.Div(
        className="position-page",
        children=[
            html.H2(title),
            html.P("Check Status when a player has been drafted. Drafted players remain visible but are grayed out."),
            dag.AgGrid(
                id=position_grid_id(position),
                rowData=get_position_rows(position),
                columnDefs=[
                    {
                        "field": "drafted",
                        "headerName": "Status",
                        "editable": True,
                        "cellRenderer": "agCheckboxCellRenderer",
                        "cellEditor": "agCheckboxCellEditor",
                    },
                    {"field": "name", "headerName": "Player name"},
                    *_health_column_def(position),
                    *_projected_points_column_defs(),
                ],
                columnSize="autoSize",
                columnSizeOptions={"skipHeader": True},
                dangerously_allow_code=True,
                defaultColDef={
                    "autoHeaderHeight": True,
                    "resizable": True,
                    "sortable": True,
                    "wrapHeaderText": True,
                },
                dashGridOptions={
                    "rowHeight": 40,
                    "getRowStyle": {
                        "function": "params.data.drafted ? {color: '#888', backgroundColor: '#f2f2f2'} : null"
                    }
                },
                style={"flex": "1 1 0", "minHeight": 0, "width": "100%"},
            ),
        ],
    )
