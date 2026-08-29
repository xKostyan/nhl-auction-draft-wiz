"""Tests for the dedicated defencemen draft table."""

import dash_ag_grid as dag

from src.data_loader import load_players
from src.pages import defencemen
from src.pages.position_table import handle_drafted_cell_change
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert defencemen.PATH == "/defencemen"
    assert defencemen.NAME == "Defencemen"
    assert defencemen.ORDER == 2


def test_layout_shows_a_position_specific_draft_grid(walk_components):
    grid = next(node for node in walk_components(defencemen.layout()) if isinstance(node, dag.AgGrid))
    assert grid.id == "d-player-grid"
    assert [column["headerName"] for column in grid.columnDefs] == ["Name", "Status"]


def test_checking_a_defenceman_uses_the_ag_grid_event_list(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "D")
    rows = handle_drafted_cell_change("D", [{"colId": "drafted", "newValue": "true", "data": {"id": str(player_id)}}])

    assert next(row for row in rows if row["id"] == player_id)["drafted"] is True
