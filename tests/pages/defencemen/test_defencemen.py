"""Tests for the dedicated defencemen draft table."""

from pathlib import Path

import dash_ag_grid as dag
from dash import dcc

from src.data_loader import load_players
from src.pages import defencemen
from src.pages.position_table import get_position_rows, handle_drafted_cell_change, handle_player_context_action
from src.storage import clear_workspace, configure_storage, get_selected_player, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert defencemen.PATH == "/defencemen"
    assert defencemen.NAME == "Defencemen"
    assert defencemen.ORDER == 2


def test_layout_shows_a_position_specific_draft_grid(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    layout = defencemen.layout()
    grid = next(node for node in walk_components(layout) if isinstance(node, dag.AgGrid))
    assert layout.className == "position-page"
    assert not any(
        getattr(node, "children", None)
        == "Check Status when a player has been drafted. Drafted players remain visible but are grayed out."
        for node in layout.children
    )
    assert grid.id == "d-player-grid"
    assert grid.className == "table-values-large position-d"
    assert grid.columnDefs[2]["cellRenderer"] == "playerNameContextMenuRenderer"
    assert grid.columnDefs[2]["cellRendererParams"] == {"allowAddToMyTeam": True}
    assert [column["headerName"] for column in grid.columnDefs] == [
        "",
        "#",
        "Player name",
        "Health (actual GP)",
        "Average Performance",
        "p TFP 2027",
        "p AFP 2027",
        "Tags",
        "Notes",
    ]
    assert grid.columnSize == "autoSize"
    assert grid.columnSizeOptions == {"skipHeader": True}
    assert grid.defaultColDef["headerClass"] == "centered-column-header"
    assert grid.defaultColDef["wrapHeaderText"] is True
    assert grid.defaultColDef["autoHeaderHeight"] is True
    assert grid.defaultColDef["cellStyle"] == {"alignItems": "center", "display": "flex"}
    assert grid.columnDefs[3]["cellRenderer"] == "actualGpSparkline"
    assert grid.columnDefs[3]["width"] == 150
    assert grid.columnDefs[3]["resizable"] is True
    assert grid.columnDefs[3]["suppressAutoSize"] is True
    assert grid.columnDefs[4] == {
        "field": "average_performance_history",
        "headerName": "Average Performance",
        "cellRenderer": "averagePerformanceChart",
        "cellRendererParams": {"scaleMaximum": 6},
        "sortable": False,
        "resizable": True,
        "suppressAutoSize": True,
        "width": 150,
    }
    assert grid.columnDefs[7]["headerName"] == "Tags"
    assert grid.columnDefs[7]["cellRenderer"] == "playerTagsRenderer"
    assert grid.columnDefs[8]["headerName"] == "Notes"
    assert grid.columnDefs[8]["editable"] is True
    assert grid.columnDefs[8]["wrapText"] is True
    assert grid.columnDefs[8]["cellStyle"]["fontSize"] == "14px"
    assert grid.columnDefs[0]["cellRenderer"] == "searchFocusCircleRenderer"
    assert grid.columnDefs[0]["width"] == 20
    assert grid.columnDefs[1]["cellRenderer"] == "draftedSwitchRenderer"
    assert grid.columnDefs[1]["resizable"] is False
    assert grid.columnDefs[1]["width"] == 26
    assert grid.dashGridOptions["rowHeight"] == 60
    assert grid.style["flex"] == "1 1 0"


def test_search_is_a_position_scoped_typeahead_and_focuses_the_selected_defenceman(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    search = next(node for node in walk_components(defencemen.layout()) if isinstance(node, dcc.Dropdown))
    player = get_position_rows("D")[0]

    assert search.id == "d-player-search"
    assert search.searchable is True
    assert search.placeholder == "Search defencemen..."
    assert {option["value"] for option in search.options} == {
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "D"
    }
    assert defencemen.focus_searched_player(player["id"]) == (
        [{"id": player["id"]}],
        {"rowId": str(player["id"]), "rowPosition": "middle", "column": "name"},
    )
    assert get_selected_player()["id"] == player["id"]


def test_select_player_context_action_updates_the_shared_graph_player(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = get_position_rows("D")[0]

    handle_player_context_action(
        "D", {"rowId": player["id"], "value": {"action": "select-player"}}
    )

    assert get_selected_player()["id"] == player["id"]


def test_context_menu_labels_the_shared_selection_action_as_highlight():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert 'menuAction("Highlight the player", "select-player")' in renderer


def test_health_renderer_displays_actual_games_played_values():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert "}, String(gamesPlayed))" in renderer
    assert 'bottom: "50%"' in renderer


def test_average_performance_renderer_has_two_skater_green_bands():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert 'actual < 3.7 ? "#f9a825" : actual < 4.1 ? "#81c784" : "#388e3c"' in renderer
    assert 'width: "100%"' in renderer


def test_checking_a_defenceman_uses_the_ag_grid_event_list(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "D")
    rows = handle_drafted_cell_change("D", [{"colId": "drafted", "value": "true", "data": {"id": str(player_id)}}])

    assert next(row for row in rows if row["id"] == player_id)["drafted"] is True


def test_drafted_switch_is_visually_on_only_for_available_players():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert "var available = !drafted" in renderer
    assert 'backgroundColor: available ? "#388e3c" : "#bdbdbd"' in renderer
    assert 'height: "calc(100% - 10px)"' in renderer
    assert "Close tag editor" in renderer
    assert 'justifyContent: "flex-start"' in renderer
    assert '}, "11px")' in renderer
