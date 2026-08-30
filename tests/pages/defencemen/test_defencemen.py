"""Tests for the dedicated defencemen draft table."""

import dash_ag_grid as dag
from dash import dcc

from src.data_loader import load_players
from src.pages import defencemen
from src.pages.position_table import get_position_rows, handle_drafted_cell_change
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


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
    assert grid.id == "d-player-grid"
    assert [column["headerName"] for column in grid.columnDefs] == [
        "Status",
        "Player name",
        "Health (actual GP)",
        "p TFP 2027",
        "p AFP 2027",
    ]
    assert grid.columnSize == "autoSize"
    assert grid.columnSizeOptions == {"skipHeader": True}
    assert grid.defaultColDef["wrapHeaderText"] is True
    assert grid.defaultColDef["autoHeaderHeight"] is True
    assert grid.columnDefs[2]["cellRenderer"] == "actualGpSparkline"
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


def test_checking_a_defenceman_uses_the_ag_grid_event_list(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "D")
    rows = handle_drafted_cell_change("D", [{"colId": "drafted", "value": "true", "data": {"id": str(player_id)}}])

    assert next(row for row in rows if row["id"] == player_id)["drafted"] is True
