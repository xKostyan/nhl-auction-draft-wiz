"""Tests for the dedicated goalies draft table."""

from pathlib import Path

import dash_ag_grid as dag
from dash import dcc

from src.data_loader import load_players
from src.pages import goalies
from src.pages.position_table import get_position_rows, handle_drafted_cell_change
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert goalies.PATH == "/goalies"
    assert goalies.NAME == "Goalies"
    assert goalies.ORDER == 3


def test_layout_shows_a_position_specific_draft_grid(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    layout = goalies.layout()
    grid = next(node for node in walk_components(layout) if isinstance(node, dag.AgGrid))
    assert layout.className == "position-page"
    assert not any(
        getattr(node, "children", None)
        == "Check Status when a player has been drafted. Drafted players remain visible but are grayed out."
        for node in layout.children
    )
    assert grid.id == "g-player-grid"
    assert grid.className == "table-values-large"
    assert [column["headerName"] for column in grid.columnDefs] == [
        "",
        "#",
        "Player name",
        "Game Starts",
        "p TFP 2027",
        "p AFP 2027",
    ]
    assert grid.columnSize == "autoSize"
    assert grid.columnSizeOptions == {"skipHeader": True}
    assert grid.defaultColDef["headerClass"] == "centered-column-header"
    assert grid.defaultColDef["wrapHeaderText"] is True
    assert grid.defaultColDef["autoHeaderHeight"] is True
    assert grid.defaultColDef["cellStyle"] == {"alignItems": "center", "display": "flex"}
    assert all(column["field"] != "actual_gp_history" for column in grid.columnDefs)
    assert grid.columnDefs[3]["cellRenderer"] == "goalieGameStartsChart"
    assert grid.columnDefs[3]["width"] == 150
    assert grid.columnDefs[3]["resizable"] is True
    assert grid.columnDefs[3]["suppressAutoSize"] is True
    assert grid.columnDefs[0]["cellRenderer"] == "searchFocusCircleRenderer"
    assert grid.columnDefs[0]["width"] == 20
    assert grid.columnDefs[1]["cellRenderer"] == "draftedSwitchRenderer"
    assert grid.columnDefs[1]["resizable"] is False
    assert grid.columnDefs[1]["width"] == 26
    assert grid.dashGridOptions["rowHeight"] == 60
    assert grid.style["flex"] == "1 1 0"


def test_search_is_a_position_scoped_typeahead_and_focuses_the_selected_goalie(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    search = next(node for node in walk_components(goalies.layout()) if isinstance(node, dcc.Dropdown))
    player = get_position_rows("G")[0]

    assert search.id == "g-player-search"
    assert search.searchable is True
    assert search.placeholder == "Search goalies..."
    assert {option["value"] for option in search.options} == {
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "G"
    }
    assert goalies.focus_searched_player(player["id"]) == (
        [{"id": player["id"]}],
        {"rowId": str(player["id"]), "rowPosition": "middle", "column": "name"},
    )


def test_goalie_rows_include_projected_and_actual_game_starts_for_every_season(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    row = next(row for row in get_position_rows("G") if row["id"] == 3634)

    assert row["game_starts_history"] == [
        {"year": 2023, "projected": 45.0, "actual": 36.0},
        {"year": 2024, "projected": 0.0, "actual": 26.0},
        {"year": 2025, "projected": 0.0, "actual": 20.0},
        {"year": 2026, "projected": 0.0, "actual": 24.0},
        {"year": 2027, "projected": 0.0, "actual": 0.0},
    ]


def test_checking_a_goalie_uses_the_ag_grid_event_list(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")
    rows = handle_drafted_cell_change("G", [{"colId": "drafted", "value": "true", "data": {"id": str(player_id)}}])

    assert next(row for row in rows if row["id"] == player_id)["drafted"] is True


def test_drafted_switch_sets_the_inverse_persisted_drafted_value():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert "props.setValue(available)" in renderer
    assert "goalieGameStartsChart" in renderer
    assert "var scaleMaximum = 70" in renderer
    assert 'stroke: "#1565c0"' in renderer
    assert 'actual < 30 ? "#d32f2f" : actual <= 42 ? "#f9a825" : "#388e3c"' in renderer
    assert 'fontSize: "9px"' in renderer
