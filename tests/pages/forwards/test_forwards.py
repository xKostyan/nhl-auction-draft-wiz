"""Tests for the dedicated forwards draft table."""

import dash_ag_grid as dag

from src.data_loader import load_players
from src.pages import forwards
from src.pages.position_table import handle_drafted_cell_change
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert forwards.PATH == "/forwards"
    assert forwards.NAME == "Forwards"
    assert forwards.ORDER == 1


def test_layout_shows_name_and_checkbox_status_columns_only(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    grid = next(node for node in walk_components(forwards.layout()) if isinstance(node, dag.AgGrid))
    assert grid.id == "f-player-grid"
    assert grid.columnDefs == [
        {"field": "name", "headerName": "Name"},
        {
            "field": "drafted",
            "headerName": "Status",
            "editable": True,
            "cellRenderer": "agCheckboxCellRenderer",
            "cellEditor": "agCheckboxCellEditor",
        },
    ]
    assert "drafted" in grid.dashGridOptions["getRowStyle"]["function"]


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
