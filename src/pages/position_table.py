"""Shared position-table presentation and status-editing helpers."""

from __future__ import annotations

import math

import dash_ag_grid as dag
from dash import dcc, html

from ..storage import (
    get_players_for_position_grid,
    get_workspace_value,
    MyTeamCapacityError,
    set_player_drafted,
    set_player_notes,
    set_player_on_my_team,
    set_player_tags,
    set_selected_player,
)

POSITION_NAMES = {"F": "Forwards", "D": "Defencemen", "G": "Goalies"}
SKATER_POSITIONS = {"F", "D"}
VERTICALLY_CENTERED_CELL_STYLE = {"alignItems": "center", "display": "flex"}
PLAYER_TAGS = {
    "F": ["PP1", "PP2", "PK1", "PK2", "Line1", "Line2"],
    "D": ["PP1", "PP2", "PK1", "PK2", "Line1", "Line2"],
    "G": ["Starter", "Backup", "1A", "1B"],
}
TAG_COLORS = {
    "PP1": "green",
    "PK1": "green",
    "Line1": "green",
    "PP2": "yellow",
    "PK2": "yellow",
    "Line2": "yellow",
    "Starter": "green",
    "1A": "green",
    "1B": "yellow",
    "Backup": "red",
}
MY_TEAM_SLOT_COUNTS = {"F": 9, "D": 5, "G": 2}
MY_TEAM_TABLES = {
    "F": {"title": "Forwards", "slots": 9, "skater_columns": True},
    "D": {"title": "Defencemen", "slots": 5, "skater_columns": True},
    "G": {"title": "Goalies", "slots": 2, "skater_columns": False},
    "utility": {"title": "Utility", "slots": 2, "skater_columns": True},
    "bench": {"title": "Bench", "slots": 4, "skater_columns": False},
}


def position_grid_id(position: str) -> str:
    """Return the stable component id for a position's player grid."""
    return f"{position.lower()}-player-grid"


def position_search_id(position: str) -> str:
    """Return the stable component id for a position's player search."""
    return f"{position.lower()}-player-search"


def position_status_id(position: str) -> str:
    """Return the status-message id for a position's player grid."""
    return f"{position.lower()}-player-action-status"


def get_position_rows(position: str, *, my_team_only: bool = False) -> list[dict]:
    """Return the current persisted player rows for one position."""
    return get_players_for_position_grid(position, my_team_only=my_team_only).to_dict("records")


def get_position_grid_rows(
    position: str, *, my_team_only: bool = False, slot_count: int | None = None
) -> list[dict]:
    """Return position rows, filling fixed My Team roster slots when requested."""
    rows = get_position_rows(position, my_team_only=my_team_only)
    if slot_count is None:
        return rows
    if not my_team_only or slot_count < 1:
        raise ValueError("Fixed player slots are only supported for a positive My Team slot count.")

    roster_rows = rows[:slot_count]
    for index, row in enumerate(roster_rows, start=1):
        row["slot_number"] = index

    for slot_number in range(len(roster_rows) + 1, slot_count + 1):
        roster_rows.append(
            {
                "id": f"empty-slot-{position}-{slot_number}",
                "slot_number": slot_number,
                "name": "Empty slot",
                "position": "",
                "is_empty_slot": True,
                "drafted": False,
                "projected_tfp": None,
                "projected_afp": None,
                "actual_gp_history": [],
                "average_performance_history": [],
                "game_starts_history": [],
                "tags": [],
                "notes": "",
            }
        )
    return roster_rows


def build_my_team_snapshot() -> dict[str, list[dict]]:
    """Load and place the complete My Team roster for one page render."""
    forwards = _sort_my_team_rows(get_position_rows("F", my_team_only=True))
    defencemen = _sort_my_team_rows(get_position_rows("D", my_team_only=True))
    goalies = _sort_my_team_rows(get_position_rows("G", my_team_only=True))
    primary_rows = {
        "F": forwards[:MY_TEAM_SLOT_COUNTS["F"]],
        "D": defencemen[:MY_TEAM_SLOT_COUNTS["D"]],
        "G": goalies[:MY_TEAM_SLOT_COUNTS["G"]],
    }
    skater_overflow = forwards[MY_TEAM_SLOT_COUNTS["F"]:] + defencemen[MY_TEAM_SLOT_COUNTS["D"]:]
    utility_rows = _sort_my_team_rows(skater_overflow)[:MY_TEAM_TABLES["utility"]["slots"]]
    bench_rows = skater_overflow[MY_TEAM_TABLES["utility"]["slots"]:] + goalies[MY_TEAM_SLOT_COUNTS["G"]:]
    table_rows = {
        **primary_rows,
        "utility": utility_rows,
        "bench": bench_rows[:MY_TEAM_TABLES["bench"]["slots"]],
    }
    return {
        table: _fill_my_team_slots(table, rows)
        for table, rows in table_rows.items()
    }


def get_my_team_table_rows(
    table: str, *, snapshot: dict[str, list[dict]] | None = None
) -> list[dict]:
    """Return fixed My Team table rows using automatic position-first placement."""
    if table not in MY_TEAM_TABLES:
        raise ValueError(f"Unsupported My Team table: {table!r}.")
    if snapshot is None:
        snapshot = build_my_team_snapshot()
    return snapshot[table]


def _sort_my_team_rows(rows: list[dict]) -> list[dict]:
    """Sort active My Team table rows by projected TFP, highest first."""
    return sorted(
        rows,
        key=lambda row: (-_finite_number(row.get("projected_tfp")), row["name"].casefold()),
    )


def get_my_team_projected_tfp_total(
    table: str, *, snapshot: dict[str, list[dict]] | None = None
) -> float:
    """Return the projected total fantasy points for a scored My Team table."""
    if table not in {"F", "D", "utility"}:
        raise ValueError(f"My Team table {table!r} does not have a projected TFP total.")
    total = 0.0
    for row in get_my_team_table_rows(table, snapshot=snapshot):
        value = row.get("projected_tfp")
        if row.get("is_empty_slot") or value is None:
            continue
        numeric_value = float(value)
        if math.isfinite(numeric_value):
            total += numeric_value
    return total


def get_my_team_goalie_projection(
    *, snapshot: dict[str, list[dict]] | None = None
) -> dict[str, float]:
    """Estimate goalie points using 90% starts shares and the 140-start cap."""
    current_season = get_workspace_value("current_season")
    active_goalies = [
        row
        for row in get_my_team_table_rows("G", snapshot=snapshot)
        if not row.get("is_empty_slot")
    ]
    bench_goalies = [
        row
        for row in get_my_team_table_rows("bench", snapshot=snapshot)
        if not row.get("is_empty_slot") and row.get("position") == "G"
    ]
    bench_goalies.sort(key=lambda row: _finite_number(row.get("projected_afp")), reverse=True)
    candidates = active_goalies + bench_goalies
    remaining_starts = 140.0
    available_starts = 0.0
    projected_points = 0.0
    for goalie in candidates:
        usable_starts = 0.9 * _goalie_projected_starts(goalie, current_season)
        available_starts += usable_starts
        counted_starts = min(usable_starts, remaining_starts)
        projected_points += counted_starts * _finite_number(goalie.get("projected_afp"))
        remaining_starts -= counted_starts
        if remaining_starts <= 0:
            break
    return {
        "projected_points": projected_points,
        "available_starts": available_starts,
        "counted_starts": min(available_starts, 140.0),
    }


def _goalie_projected_starts(goalie: dict, current_season: str) -> float:
    """Return a goalie's projected starts for the detected draft season."""
    for season in goalie.get("game_starts_history", []):
        if str(season.get("year")) == current_season:
            return _finite_number(season.get("projected"))
    return 0.0


def _finite_number(value: object) -> float:
    """Return a finite numeric value, treating missing data as zero."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return numeric_value if math.isfinite(numeric_value) else 0.0


def get_my_team_table_title(
    table: str, *, snapshot: dict[str, list[dict]] | None = None
) -> str:
    """Return a readable My Team heading for callers that require plain text."""
    title, projection_label, projected_total = get_my_team_table_heading(
        table, snapshot=snapshot
    )
    return " ".join(part for part in (title, projection_label, projected_total) if part)


def get_my_team_table_heading(
    table: str, *, snapshot: dict[str, list[dict]] | None = None
) -> tuple[str, str, str]:
    """Return aligned My Team heading title, projection label, and total."""
    if table not in MY_TEAM_TABLES:
        raise ValueError(f"Unsupported My Team table: {table!r}.")
    title = MY_TEAM_TABLES[table]["title"]
    if table == "bench":
        return title, "", ""

    projection_label = "projection:"
    if table == "G":
        projection = get_my_team_goalie_projection(snapshot=snapshot)
        if projection["available_starts"] < 140:
            projection_label = (
                f"{projection_label} (Warning: projected starts "
                f"{projection['counted_starts']:.1f}/140)"
            )
        return title, projection_label, f"{projection['projected_points']:.2f}"
    return (
        title,
        projection_label,
        f"{get_my_team_projected_tfp_total(table, snapshot=snapshot):.2f}",
    )


def _fill_my_team_slots(table: str, player_rows: list[dict]) -> list[dict]:
    """Add stable indices and visible vacancy rows to a fixed My Team table."""
    table_config = MY_TEAM_TABLES[table]
    rows = player_rows[:table_config["slots"]]
    for index, row in enumerate(rows, start=1):
        row["slot_number"] = index

    for slot_number in range(len(rows) + 1, table_config["slots"] + 1):
        rows.append(
            {
                "id": f"empty-slot-{table}-{slot_number}",
                "slot_number": slot_number,
                "name": "Empty slot",
                "is_empty_slot": True,
                "drafted": False,
                "on_my_team": False,
                "projected_tfp": None,
                "projected_afp": None,
                "actual_gp_history": [],
                "average_performance_history": [],
                "game_starts_history": [],
                "tags": [],
                "notes": "",
            }
        )
    return rows


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


def select_searched_player(position: str, player_id: object) -> tuple[list[dict], dict | None]:
    """Persist a search-selected player and return its AG Grid focus targets."""
    selected_rows, scroll_target = get_player_search_target(position, player_id)
    if player_id is not None:
        set_selected_player(_parse_player_id(player_id))
    return selected_rows, scroll_target


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


def _projected_game_starts_column_def(position: str) -> list[dict]:
    """Return the upcoming projected game-starts column for goalies."""
    if position != "G":
        return []
    return [{"field": "projected_gs", "headerName": "p GS", "type": "numericColumn"}]


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
            "resizable": True,
            "suppressAutoSize": True,
            "width": 150,
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


def _tags_column_def(position: str) -> list[dict]:
    """Return the editable persistent player tags column."""
    return [
        {
            "field": "tags",
            "headerName": "Tags",
            "cellRenderer": "playerTagsRenderer",
            "cellRendererParams": {"availableTags": PLAYER_TAGS[position], "tagColors": TAG_COLORS},
            "sortable": False,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 160,
        }
    ]


def _notes_column_def(*, disable_empty_slots: bool = False) -> list[dict]:
    """Return the editable wrapped player notes column."""
    return [
        {
            "field": "notes",
            "headerName": "Notes",
            "cellEditor": "agLargeTextCellEditor",
            "cellEditorPopup": True,
            "cellEditorParams": {"maxLength": 1000, "rows": 4, "cols": 30},
            "cellStyle": {
                "alignItems": "center",
                "display": "flex",
                "fontSize": "14px",
                "lineHeight": "18px",
                "whiteSpace": "normal",
            },
            "editable": (
                {"function": "!params.data.is_empty_slot"} if disable_empty_slots else True
            ),
            "resizable": True,
            "suppressAutoSize": True,
            "width": 220,
            "wrapText": True,
        }
    ]


def _player_name_column_def(*, allow_add_to_my_team: bool) -> dict:
    """Return the player-name column with its shared custom context menu."""
    return {
        "field": "name",
        "headerName": "Player name",
        "cellRenderer": "playerNameContextMenuRenderer",
        "cellRendererParams": {"allowAddToMyTeam": allow_add_to_my_team},
    }


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


def _parse_player_tags(position: str, value: object) -> list[str]:
    """Validate a JSON-compatible tag list emitted by the grid renderer."""
    if not isinstance(value, list) or any(not isinstance(tag, str) for tag in value):
        raise ValueError("Player tag updates require a list of tag names.")
    if len(value) != len(set(value)) or any(tag not in PLAYER_TAGS[position] for tag in value):
        raise ValueError("Player tag updates require unique recognized tag names.")
    return value


def _parse_context_action(value: object) -> str:
    """Extract the action from the timestamp-suffixed browser menu payload."""
    if not isinstance(value, str):
        raise ValueError("Player context-menu updates require an action.")
    action = value.split(":", 1)[0]
    if action not in {
        "clear-tags",
        "clear-notes",
        "add-to-my-team",
        "remove-from-my-team",
        "select-player",
    }:
        raise ValueError("Player context-menu action is not recognized.")
    return action


def handle_player_context_action(
    position: str,
    context_action: dict | None,
    *,
    my_team_only: bool = False,
    slot_count: int | None = None,
) -> list[dict]:
    """Persist a custom player-name menu action emitted by the cell renderer."""
    persist_player_context_action(position, context_action)
    return get_position_grid_rows(position, my_team_only=my_team_only, slot_count=slot_count)


def persist_player_context_action(position: str, context_action: dict | None) -> None:
    """Persist a custom player-name menu action without reloading grid rows."""
    if not context_action:
        return
    if not isinstance(context_action, dict):
        raise ValueError("Player context-menu updates require an event dictionary.")

    player_id = _parse_player_id(context_action.get("rowId"))
    value = context_action.get("value")
    if not isinstance(value, dict):
        raise ValueError("Player context-menu updates require an action payload.")
    action = _parse_context_action(value.get("action"))
    if action == "select-player":
        set_selected_player(player_id)
    elif action == "clear-tags":
        set_player_tags(player_id, [])
    elif action == "clear-notes":
        set_player_notes(player_id, "")
    else:
        set_player_on_my_team(player_id, action == "add-to-my-team")


def handle_player_cell_change(
    position: str,
    cell_changes: list[dict] | None,
    *,
    my_team_only: bool = False,
    slot_count: int | None = None,
) -> list[dict]:
    """Persist drafted and tag cell edits and return fresh grid rows.

    Dash AG Grid provides ``cellValueChanged`` as a list of event dictionaries,
    even when exactly one cell was changed. Process every event because a
    clipboard action can update multiple status cells in one callback.
    """
    persist_player_cell_changes(position, cell_changes)
    return get_position_grid_rows(position, my_team_only=my_team_only, slot_count=slot_count)


def persist_player_cell_changes(position: str, cell_changes: list[dict] | None) -> None:
    """Persist grid cell changes without reloading grid rows."""
    if not cell_changes:
        return
    for cell_change in cell_changes:
        if not isinstance(cell_change, dict):
            raise ValueError("Drafted status updates require an AG Grid event dictionary.")
        column_id = cell_change.get("colId")
        if column_id not in {"drafted", "notes", "tags", "context_action"}:
            continue

        row_data = cell_change.get("data") or {}
        if not isinstance(row_data, dict):
            raise ValueError("Drafted status updates require AG Grid row data.")

        player_id = _parse_player_id(row_data.get("id"))
        value = cell_change.get("newValue")
        if value is None:
            value = cell_change.get("value")
        if column_id == "drafted":
            set_player_drafted(player_id, _parse_drafted_value(value))
        elif column_id == "tags":
            set_player_tags(player_id, _parse_player_tags(position, value))
        elif column_id == "context_action":
            action = _parse_context_action(value)
            if action == "clear-tags":
                set_player_tags(player_id, [])
            elif action == "clear-notes":
                set_player_notes(player_id, "")
            else:
                set_player_on_my_team(player_id, action == "add-to-my-team")
        elif not isinstance(value, str):
            raise ValueError("Player note updates require text.")
        else:
            set_player_notes(player_id, value)


def handle_player_grid_update(
    position: str,
    cell_changes: list[dict] | None,
    context_action: dict | None,
    triggered_property: str,
    *,
    my_team_only: bool = False,
    slot_count: int | None = None,
) -> list[dict]:
    """Dispatch only the grid property that initiated this callback.

    Dash retains the most recent value for each Input. A previous context-menu
    payload must not be reapplied when a later Tags or Notes edit triggers the
    same callback.
    """
    if triggered_property == "cellRendererData":
        return handle_player_context_action(
            position, context_action, my_team_only=my_team_only, slot_count=slot_count
        )
    if triggered_property == "cellValueChanged":
        return handle_player_cell_change(
            position, cell_changes, my_team_only=my_team_only, slot_count=slot_count
        )
    raise ValueError(f"Unsupported player-grid trigger: {triggered_property!r}.")


def handle_player_grid_update_with_message(
    position: str, cell_changes: list[dict] | None, context_action: dict | None, triggered_property: str
) -> tuple[list[dict], str]:
    """Return a visible capacity message instead of failing a stale add request."""
    try:
        return handle_player_grid_update(position, cell_changes, context_action, triggered_property), ""
    except MyTeamCapacityError as error:
        return get_position_rows(position), str(error)


handle_drafted_cell_change = handle_player_cell_change


def build_position_grid(
    position: str, *, my_team_only: bool = False, slot_count: int | None = None
) -> dag.AgGrid:
    """Build one reusable position grid, optionally restricted to My Team."""
    if slot_count is not None and (not my_team_only or slot_count < 1):
        raise ValueError("Fixed player slots are only supported for a positive My Team slot count.")
    grid_style = {"flex": "1 1 0", "minHeight": 0, "width": "100%"}
    if slot_count is not None:
        grid_style.update({"flex": "0 0 auto", "height": f"{slot_count * 40 + 50}px"})

    return dag.AgGrid(
        id=position_grid_id(position) if not my_team_only else f"my-team-{position.lower()}-player-grid",
        className=f"table-values-large position-{position.lower()}",
        rowData=get_position_grid_rows(
            position, my_team_only=my_team_only, slot_count=slot_count
        ),
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
            *([] if my_team_only else [{
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
            }]),
            *([] if slot_count is None else [{
                "field": "slot_number",
                "headerName": "",
                "type": "numericColumn",
                "sortable": False,
                "resizable": False,
                "width": 32,
            }]),
            _player_name_column_def(allow_add_to_my_team=not my_team_only),
            *_health_column_def(position),
            *_game_starts_column_def(position),
            *_average_performance_column_def(position),
            *_projected_game_starts_column_def(position),
            *_projected_points_column_defs(),
            *_tags_column_def(position),
            *_notes_column_def(disable_empty_slots=slot_count is not None),
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
            "rowHeight": 40 if slot_count is not None else 60,
            "rowSelection": {
                "mode": "singleRow",
                "checkboxes": False,
                "headerCheckbox": False,
            },
            **({
                "getRowStyle": {
                    "function": (
                        "params.data.is_empty_slot ? "
                        "{color: '#999', backgroundColor: '#f2f2f2', fontStyle: 'italic'} : null"
                    )
                }
            } if slot_count is not None else {} if my_team_only else {
                "getRowStyle": {
                    "function": "params.data.drafted ? {color: '#888', backgroundColor: '#f2f2f2'} : null"
                }
            }),
        },
        style=grid_style,
    )


def build_my_team_grid(
    table: str, *, snapshot: dict[str, list[dict]] | None = None
) -> dag.AgGrid:
    """Build one fixed My Team position, utility, or bench roster table."""
    if table not in MY_TEAM_TABLES:
        raise ValueError(f"Unsupported My Team table: {table!r}.")
    config = MY_TEAM_TABLES[table]
    is_skater_table = config["skater_columns"]
    is_goalie_table = table == "G"
    tag_position = "G" if is_goalie_table else "F"
    column_defs = [
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
            "field": "slot_number",
            "headerName": "",
            "type": "numericColumn",
            "sortable": False,
            "resizable": False,
            "width": 32,
        },
        _player_name_column_def(allow_add_to_my_team=False),
        *([{"field": "position", "headerName": "Position"}] if table in {"utility", "bench"} else []),
        *(_health_column_def("F") if is_skater_table else []),
        *(_game_starts_column_def("G") if is_goalie_table else []),
        *(_average_performance_column_def(tag_position) if is_skater_table or is_goalie_table else []),
        *(_projected_game_starts_column_def("G") if is_goalie_table else []),
        *_projected_points_column_defs(),
        *(_tags_column_def(tag_position) if is_skater_table or is_goalie_table else []),
        *(_notes_column_def(disable_empty_slots=True) if is_skater_table or is_goalie_table else []),
    ]
    return dag.AgGrid(
        id=f"my-team-{table.lower()}-player-grid",
        className=f"table-values-large my-team-table-{table}",
        rowData=get_my_team_table_rows(table, snapshot=snapshot),
        getRowId="params.data.id",
        columnDefs=column_defs,
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
            "rowHeight": 50,
            "suppressVerticalScroll": True,
            "rowSelection": {
                "mode": "singleRow",
                "checkboxes": False,
                "headerCheckbox": False,
            },
            "getRowStyle": {
                "function": (
                    "params.data.is_empty_slot ? "
                    "{color: '#999', backgroundColor: '#f2f2f2', fontStyle: 'italic'} : null"
                )
            },
        },
        style={
            "flex": "0 0 auto",
            "height": f"{config['slots'] * 50 + 50}px",
            "minHeight": 0,
            "width": "100%",
        },
    )


def handle_my_team_grid_update(
    table: str,
    cell_changes: list[dict] | None,
    context_action: dict | None,
    triggered_property: str,
) -> list[dict]:
    """Persist a My Team table event and return its automatically placed rows."""
    persist_my_team_grid_update(table, cell_changes, context_action, triggered_property)
    return get_my_team_table_rows(table)


def persist_my_team_grid_update(
    table: str,
    cell_changes: list[dict] | None,
    context_action: dict | None,
    triggered_property: str,
) -> None:
    """Persist a My Team grid event without loading an unused position grid."""
    if table not in MY_TEAM_TABLES:
        raise ValueError(f"Unsupported My Team table: {table!r}.")
    tag_position = "G" if table == "G" else "F"
    if triggered_property == "cellRendererData":
        persist_player_context_action(tag_position, context_action)
    elif triggered_property == "cellValueChanged":
        persist_player_cell_changes(tag_position, cell_changes)
    else:
        raise ValueError(f"Unsupported player-grid trigger: {triggered_property!r}.")


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
            html.Div(id=position_status_id(position), role="status"),
            build_position_grid(position),
        ],
    )
