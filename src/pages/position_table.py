"""Shared position-table presentation and status-editing helpers."""

from __future__ import annotations

import dash_ag_grid as dag
from dash import dcc, html

from ..storage import (
    get_players_for_position_grid,
    get_workspace_value,
    set_player_drafted,
)

POSITION_NAMES = {"F": "Forwards", "D": "Defencemen", "G": "Goalies"}
SKATER_POSITIONS = {"F", "D"}
VERTICALLY_CENTERED_CELL_STYLE = {"alignItems": "center", "display": "flex"}


def position_grid_id(position: str) -> str:
    """Return the stable component id for a position's player grid."""
    return f"{position.lower()}-player-grid"


def position_search_id(position: str) -> str:
    """Return the stable component id for a position's player search."""
    return f"{position.lower()}-player-search"


def get_position_rows(position: str) -> list[dict]:
    """Return the current persisted player rows for one position."""
    return get_players_for_position_grid(position).to_dict("records")


def get_position_search_options(position: str) -> list[dict]:
    """Return searchable player options limited to one position."""
    return [
        {"label": row["name"], "value": row["id"]}
        for row in sorted(get_position_rows(position), key=lambda row: row["name"].casefold())
    ]


def get_player_search_target(position: str, player_id: object) -> tuple[list[dict], dict | None]:
    """Return AG Grid selection and scroll targets for a selected player."""
    if player_id is None:
        return [], None

    selected_id = _parse_player_id(player_id)
    for row in get_position_rows(position):
        if row["id"] == selected_id:
            return [{"id": selected_id}], {
                "rowId": str(selected_id),
                "rowPosition": "middle",
                "column": "name",
            }
    raise ValueError(f"Player {selected_id} is not a {POSITION_NAMES[position].lower()} player.")


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
            "width": 110,
        }
    ]


def _game_starts_column_def(position: str) -> list[dict]:
    """Return the projected-line and actual-bar game-starts chart for goalies."""
    if position != "G":
        return []
    return [
        {
            "field": "game_starts_history",
            "headerName": "Game Starts",
            "cellRenderer": "goalieGameStartsChart",
            "sortable": False,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 150,
        }
    ]


def _average_performance_column_def(position: str) -> list[dict]:
    """Return projected-line and actual-bar average-performance chart settings."""
    return [
        {
            "field": "average_performance_history",
            "headerName": "Average Performance",
            "cellRenderer": "averagePerformanceChart",
            "cellRendererParams": {"scaleMaximum": 12 if position == "G" else 6},
            "sortable": False,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 150,
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
            dcc.Dropdown(
                id=position_search_id(position),
                options=get_position_search_options(position),
                placeholder=f"Search {title.lower()}...",
                searchable=True,
                clearable=True,
                className="player-search",
            ),
            dag.AgGrid(
                id=position_grid_id(position),
                className="table-values-large",
                rowData=get_position_rows(position),
                getRowId="params.data.id",
                columnDefs=[
                    {
                        "field": "search_focus",
                        "headerName": "",
                        "cellRenderer": "searchFocusCircleRenderer",
                        "sortable": False,
                        "resizable": False,
                        "suppressMenu": True,
                        "width": 20,
                    },
                    {
                        "field": "drafted",
                        "headerName": "#",
                        "cellRenderer": "draftedSwitchRenderer",
                        "cellStyle": {
                            **VERTICALLY_CENTERED_CELL_STYLE,
                            "paddingLeft": "2px",
                            "paddingRight": "2px",
                        },
                        "resizable": False,
                        "width": 26,
                    },
                    {"field": "name", "headerName": "Player name"},
                    *_health_column_def(position),
                    *_game_starts_column_def(position),
                    *_average_performance_column_def(position),
                    *_projected_points_column_defs(),
                ],
                columnSize="autoSize",
                columnSizeOptions={"skipHeader": True},
                dangerously_allow_code=True,
                defaultColDef={
                    "autoHeaderHeight": True,
                    "cellStyle": VERTICALLY_CENTERED_CELL_STYLE,
                    "headerClass": "centered-column-header",
                    "resizable": True,
                    "sortable": True,
                    "wrapHeaderText": True,
                },
                dashGridOptions={
                    "rowHeight": 60,
                    "rowSelection": {
                        "mode": "singleRow",
                        "checkboxes": False,
                        "headerCheckbox": False,
                    },
                    "getRowStyle": {
                        "function": "params.data.drafted ? {color: '#888', backgroundColor: '#f2f2f2'} : null"
                    }
                },
                style={"flex": "1 1 0", "minHeight": 0, "width": "100%"},
            ),
        ],
    )
