"""Tests for the Player stats table page."""

import dash_ag_grid as dag
from dash import dcc

from src.pages import player_stats_table
from src.storage import (
    clear_workspace,
    configure_storage,
    get_players_for_stat_lookup,
    import_yearly_dataset,
)


def test_page_is_registered_at_the_expected_path_and_order():
    assert player_stats_table.PATH == "/player-stats-table"
    assert player_stats_table.NAME == "Player stats table"
    assert player_stats_table.ORDER == 5


def test_layout_exposes_an_all_player_search_and_an_empty_stats_grid(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    layout = player_stats_table.layout()
    search = next(node for node in walk_components(layout) if isinstance(node, dcc.Dropdown))
    grid = next(node for node in walk_components(layout) if isinstance(node, dag.AgGrid))

    assert layout.className == "player-stats-page"
    assert search.id == player_stats_table.PLAYER_SEARCH_ID
    assert search.searchable is True
    assert search.placeholder == "Search players..."
    assert {option["value"] for option in search.options} == {
        int(row.id) for row in get_players_for_stat_lookup().itertuples(index=False)
    }
    assert grid.id == player_stats_table.GRID_ID
    assert grid.rowData == []
    assert grid.columnDefs == [
        {"field": "year", "headerName": "year", "type": "numericColumn"},
        {"field": "stats_type", "headerName": "stats_type"},
    ]
    assert grid.defaultColDef == {"resizable": True, "sortable": True, "width": 100}


def test_selected_player_generates_a_dynamic_stats_table(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player = get_players_for_stat_lookup().iloc[0]
    rows, column_defs = player_stats_table.build_player_stats_table(int(player["id"]))

    fields = [column["field"] for column in column_defs]
    assert rows
    assert fields[:2] == ["year", "stats_type"]
    assert {"GP", "FP", "FP_AVG"}.issubset(fields)
    assert all(set(row).issubset(set(fields)) for row in rows)
    assert all(isinstance(row["year"], int) for row in rows)
    assert {row["stats_type"] for row in rows}.issubset({"actual", "projected"})


def test_no_player_selection_leaves_the_table_empty():
    rows, column_defs = player_stats_table.build_player_stats_table(None)

    assert rows == []
    assert [column["field"] for column in column_defs] == ["year", "stats_type"]
