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
)
from src.storage import (
    clear_workspace,
    configure_storage,
    get_workspace_value,
    import_yearly_dataset,
)


def test_page_is_registered_at_the_expected_path_and_order():
    assert forwards.PATH == "/forwards"
    assert forwards.NAME == "Forwards"
    assert forwards.ORDER == 1


def test_layout_shows_current_season_projected_points_and_checkbox_status_columns(tmp_path, walk_components):
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
    assert grid.columnDefs == [
        {
            "field": "drafted",
            "headerName": "#",
            "editable": True,
            "cellRenderer": "agCheckboxCellRenderer",
            "cellEditor": "agCheckboxCellEditor",
        },
        {"field": "name", "headerName": "Player name"},
        {
            "field": "actual_gp_history",
            "headerName": "Health (actual GP)",
            "cellRenderer": "actualGpSparkline",
            "sortable": False,
            "resizable": False,
            "width": 132,
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
    ]
    assert grid.columnSize == "autoSize"
    assert grid.columnSizeOptions == {"skipHeader": True}
    assert grid.defaultColDef == {
        "autoHeaderHeight": True,
        "headerClass": "centered-column-header",
        "resizable": True,
        "sortable": True,
        "wrapHeaderText": True,
    }
    assert grid.dangerously_allow_code is True
    assert grid.dashGridOptions["rowHeight"] == 30
    assert grid.dashGridOptions["rowSelection"] == {"mode": "singleRow"}
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


def test_health_renderer_returns_react_bars_with_four_availability_colors():
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
    assert 'padding: "1px 4px"' in renderer


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
