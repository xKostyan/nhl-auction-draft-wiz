"""Tests for the dedicated defencemen draft table."""

import dash_ag_grid as dag

from src.pages import defencemen


def test_page_is_registered_at_the_expected_path_and_order():
    assert defencemen.PATH == "/defencemen"
    assert defencemen.NAME == "Defencemen"
    assert defencemen.ORDER == 2


def test_layout_shows_a_position_specific_draft_grid(walk_components):
    grid = next(node for node in walk_components(defencemen.layout()) if isinstance(node, dag.AgGrid))
    assert grid.id == "d-player-grid"
    assert [column["headerName"] for column in grid.columnDefs] == ["Name", "Status"]
