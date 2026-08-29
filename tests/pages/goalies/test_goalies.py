"""Tests for the dedicated goalies draft table."""

import dash_ag_grid as dag

from src.data_loader import load_players
from src.pages import goalies
from src.pages.position_table import handle_drafted_cell_change
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert goalies.PATH == "/goalies"
    assert goalies.NAME == "Goalies"
    assert goalies.ORDER == 3


def test_layout_shows_a_position_specific_draft_grid(walk_components):
    layout = goalies.layout()
    grid = next(node for node in walk_components(layout) if isinstance(node, dag.AgGrid))
    assert layout.className == "position-page"
    assert grid.id == "g-player-grid"
    assert [column["headerName"] for column in grid.columnDefs] == ["Name", "Status"]
    assert grid.style["flex"] == "1 1 0"


def test_checking_a_goalie_uses_the_ag_grid_event_list(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")
    rows = handle_drafted_cell_change("G", [{"colId": "drafted", "value": "true", "data": {"id": str(player_id)}}])

    assert next(row for row in rows if row["id"] == player_id)["drafted"] is True
