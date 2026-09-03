"""Tests for the dedicated forwards draft table."""

from pathlib import Path

import dash_ag_grid as dag
from dash import dcc

from src.data_loader import load_players
from src.pages import forwards
from src.pages.position_table import (
    get_player_search_target,
    get_position_rows,
    handle_drafted_cell_change,
    handle_player_context_action,
    handle_player_grid_update,
)
from src.storage import (
    clear_workspace,
    configure_storage,
    get_selected_player,
    get_workspace_value,
    import_yearly_dataset,
)


def test_page_is_registered_at_the_expected_path_and_order():
    assert forwards.PATH == "/forwards"
    assert forwards.NAME == "Forwards"
    assert forwards.ORDER == 1


def test_layout_shows_current_season_projected_points_and_switch_status_columns(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    grid = next(node for node in walk_components(forwards.layout()) if isinstance(node, dag.AgGrid))
    assert forwards.layout().className == "position-page"
    assert not any(
        getattr(node, "children", None)
        == "Check Status when a player has been drafted. Drafted players remain visible but are grayed out."
        for node in forwards.layout().children
    )
    assert grid.id == "f-player-grid"
    assert grid.className == "table-values-large position-f"
    assert grid.columnDefs == [
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
                "alignItems": "center",
                "display": "flex",
                "paddingLeft": "2px",
                "paddingRight": "2px",
            },
            "resizable": False,
            "width": 26,
        },
        {
            "field": "name",
            "headerName": "Player name",
            "cellRenderer": "playerNameContextMenuRenderer",
            "cellRendererParams": {"allowAddToMyTeam": True},
        },
        {
            "field": "actual_gp_history",
            "headerName": "Health (actual GP)",
            "cellRenderer": "actualGpSparkline",
            "sortable": False,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 150,
        },
        {
            "field": "average_performance_history",
            "headerName": "Average Performance",
            "cellRenderer": "averagePerformanceChart",
            "cellRendererParams": {"scaleMaximum": 6},
            "sortable": False,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 150,
        },
        {
            "field": "projected_tfp",
            "headerName": "p TFP 2027",
            "type": "numericColumn",
        },
        {
            "field": "projected_afp",
            "headerName": "p AFP 2027",
            "type": "numericColumn",
        },
        {
            "field": "tags",
            "headerName": "Tags",
            "cellRenderer": "playerTagsRenderer",
            "cellRendererParams": {
                "availableTags": ["PP1", "PP2", "PK1", "PK2", "Line1", "Line2"],
                "tagColors": {
                    "PP1": "green", "PK1": "green", "Line1": "green",
                    "PP2": "yellow", "PK2": "yellow", "Line2": "yellow",
                    "Starter": "green", "1A": "green", "1B": "yellow", "Backup": "red",
                },
            },
            "sortable": False,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 160,
        },
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
            "editable": True,
            "resizable": True,
            "suppressAutoSize": True,
            "width": 220,
            "wrapText": True,
        },
    ]
    assert grid.columnSize == "autoSize"
    assert grid.columnSizeOptions == {"skipHeader": True}
    assert grid.defaultColDef == {
        "autoHeaderHeight": True,
        "cellStyle": {"alignItems": "center", "display": "flex"},
        "headerClass": "centered-column-header",
        "resizable": True,
        "sortable": True,
        "wrapHeaderText": True,
    }
    assert grid.dangerously_allow_code is True
    assert grid.dashGridOptions["rowHeight"] == 60
    assert grid.dashGridOptions["rowSelection"] == {
        "mode": "singleRow",
        "checkboxes": False,
        "headerCheckbox": False,
    }
    assert grid.getRowId == "params.data.id"
    assert "drafted" in grid.dashGridOptions["getRowStyle"]["function"]
    assert grid.style == {"flex": "1 1 0", "minHeight": 0, "width": "100%"}


def test_search_is_a_position_scoped_typeahead_and_focuses_the_selected_forward(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    layout = forwards.layout()
    search = next(node for node in walk_components(layout) if isinstance(node, dcc.Dropdown))
    player = next(row for row in get_position_rows("F") if row["name"] == "Mikko Rantanen")

    assert search.id == "f-player-search"
    assert search.searchable is True
    assert search.placeholder == "Search forwards..."
    assert {option["value"] for option in search.options} == {
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "F"
    }
    assert forwards.focus_searched_player(player["id"]) == (
        [{"id": player["id"]}],
        {"rowId": str(player["id"]), "rowPosition": "middle", "column": "name"},
    )
    assert get_selected_player()["id"] == player["id"]
    assert get_player_search_target("F", None) == ([], None)


def test_rows_include_current_season_projected_fantasy_points(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    row = next(row for row in get_position_rows("F") if row["name"] == "Mikko Rantanen")
    assert row["projected_tfp"] == 322.65
    assert row["projected_afp"] == 4.54
    assert get_workspace_value("current_season") == "2027"


def test_skater_rows_include_the_five_most_recent_actual_gp_seasons(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    history = next(
        row["actual_gp_history"]
        for row in get_position_rows("F")
        if row["name"] == "Mikko Rantanen"
    )
    assert history == [
        {"year": 2026, "games_played": 64.0},
        {"year": 2025, "games_played": 82.0},
        {"year": 2024, "games_played": 80.0},
        {"year": 2023, "games_played": 82.0},
    ]


def test_forward_rows_include_average_performance_for_every_season(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    history = next(
        row["average_performance_history"]
        for row in get_position_rows("F")
        if row["name"] == "Mikko Rantanen"
    )

    assert [season["year"] for season in history] == [2023, 2024, 2025, 2026, 2027]
    assert history[-1]["projected"] == 4.54
    assert history[-1]["actual"] == 0.0


def test_grid_renderers_include_health_bars_drafted_switch_and_search_focus_circle():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert "dashAgGridComponentFunctions" in renderer
    assert "dashAgGridFunctions" not in renderer
    assert "React.createElement" in renderer
    assert "document.createElement" not in renderer
    assert "#d32f2f" in renderer
    assert "#ef6c00" in renderer
    assert "#f9a825" in renderer
    assert "#388e3c" in renderer
    assert 'actual < 3.7 ? "#f9a825" : actual < 4.1 ? "#81c784" : "#388e3c"' in renderer
    assert 'boxSizing: "border-box"' in renderer
    assert 'height: "calc(100% - 10px)"' in renderer
    assert 'padding: "1px 4px"' in renderer
    assert "}, String(gamesPlayed))" in renderer
    assert 'gap: "1px"' in renderer
    assert 'justifyContent: "center",\n            padding: "1px 4px",\n            width: "100%"' in renderer
    assert "draftedSwitchRenderer" in renderer
    assert "searchFocusCircleRenderer" in renderer
    assert 'onMyTeam ? "#90caf9" : "#d3d3d3"' in renderer
    assert "averagePerformanceChart" in renderer
    assert "scaleMaximum === 6" in renderer
    assert "var scaleMaximum = props.scaleMaximum" in renderer
    assert "playerTagsRenderer" in renderer
    assert "playerNameContextMenuRenderer" in renderer
    assert 'menuAction("Highlight the player", "select-player")' in renderer
    assert "props.node.setData(Object.assign({}, props.data" in renderer
    assert 'on_my_team: action === "add-to-my-team"' in renderer
    assert "props.setData({ action: action, timestamp: Date.now() })" in renderer
    assert 'props.setData({ action: "select-player", timestamp: Date.now() })' in renderer
    assert 'if (action === "select-player") {' in renderer
    assert "props.node.setSelected(true, true);" in renderer
    assert "ReactDOM.createPortal" in renderer
    assert 'position: "fixed"' in renderer
    assert 'zIndex: "10000"' in renderer
    assert 'document.addEventListener("mousedown", closeOnOutsideLeftClick)' in renderer
    assert "event.button === 0" in renderer
    assert "#a5d6a7" in renderer
    assert "#fff59d" in renderer
    assert "#ef9a9a" in renderer
    assert '}, "11px")' in renderer
    assert "Close tag editor" in renderer
    assert '}, "Done")' in renderer
    assert 'justifyContent: "flex-start"' in renderer
    assert "var available = !drafted" in renderer
    assert "props.setValue(available)" in renderer
    assert 'backgroundColor: selected ? "#388e3c" : onMyTeam ? "#90caf9" : "#d3d3d3"' in renderer


def test_checking_a_forward_marks_it_drafted_and_keeps_it_in_the_grid(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "F"
    )
    rows = handle_drafted_cell_change(
        "F", [{"colId": "drafted", "newValue": True, "data": {"id": player_id}}]
    )

    player = next(row for row in rows if row["id"] == player_id)
    assert player["drafted"] is True


def test_checking_a_forward_accepts_dash_ag_grid_value_event(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "F"
    )
    rows = handle_drafted_cell_change(
        "F", [{"colId": "drafted", "value": "true", "data": {"id": str(player_id)}}]
    )

    assert next(row for row in rows if row["id"] == player_id)["drafted"] is True


def test_batch_status_edits_persist_every_forward_change(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_ids = [
        int(row.id)
        for row in load_players().itertuples(index=False)
        if row.position == "F"
    ][:2]
    rows = handle_drafted_cell_change(
        "F",
        [
            {"colId": "drafted", "value": "true", "data": {"id": str(player_id)}}
            for player_id in player_ids
        ],
    )

    drafted_player_ids = {row["id"] for row in rows if row["drafted"]}
    assert set(player_ids).issubset(drafted_player_ids)


def test_tag_changes_persist_for_a_forward(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    rows = handle_drafted_cell_change(
        "F", [{"colId": "tags", "value": ["PP1", "Line2"], "data": {"id": player_id}}]
    )

    assert next(row for row in rows if row["id"] == player_id)["tags"] == ["Line2", "PP1"]


def test_note_changes_persist_for_a_forward(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    rows = handle_drafted_cell_change(
        "F", [{"colId": "notes", "value": "Top power-play unit.", "data": {"id": player_id}}]
    )

    assert next(row for row in rows if row["id"] == player_id)["notes"] == "Top power-play unit."


def test_player_context_actions_persist_for_a_forward(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    handle_drafted_cell_change("F", [
        {"colId": "tags", "value": ["PP1"], "data": {"id": player_id}},
        {"colId": "notes", "value": "Keep", "data": {"id": player_id}},
    ])
    handle_player_context_action("F", {"rowId": player_id, "value": {"action": "clear-tags"}})
    handle_player_context_action("F", {"rowId": player_id, "value": {"action": "clear-notes"}})
    handle_player_context_action("F", {"rowId": player_id, "value": {"action": "add-to-my-team"}})

    player = next(row for row in get_position_rows("F") if row["id"] == player_id)
    assert player["tags"] == []
    assert player["notes"] == ""
    assert player["drafted"] is True


def test_select_player_context_action_updates_the_shared_graph_player(tmp_path):
    from src.storage import get_selected_player

    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = get_position_rows("F")[0]

    handle_player_context_action(
        "F", {"rowId": player["id"], "value": {"action": "select-player"}}
    )

    assert get_selected_player()["id"] == player["id"]


def test_cell_edit_is_not_blocked_by_a_previous_context_action(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")

    rows = handle_player_grid_update(
        "F",
        [{"colId": "tags", "value": ["PP1"], "data": {"id": player_id}}],
        {"rowId": player_id, "value": {"action": "clear-tags"}},
        "cellValueChanged",
    )

    assert next(row for row in rows if row["id"] == player_id)["tags"] == ["PP1"]


def test_context_event_is_dispatched_without_reapplying_on_later_cell_edits(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")

    handle_player_grid_update(
        "F",
        None,
        {"rowId": player_id, "value": {"action": "clear-notes"}},
        "cellRendererData",
    )
    rows = handle_player_grid_update(
        "F",
        [{"colId": "notes", "value": "New note", "data": {"id": player_id}}],
        {"rowId": player_id, "value": {"action": "clear-notes"}},
        "cellValueChanged",
    )

    assert next(row for row in rows if row["id"] == player_id)["notes"] == "New note"
