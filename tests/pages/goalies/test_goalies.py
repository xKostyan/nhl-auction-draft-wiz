"""Tests for the dedicated goalies draft table."""

import dash_ag_grid as dag

from src.pages import goalies


def test_page_is_registered_at_the_expected_path_and_order():
    assert goalies.PATH == "/goalies"
    assert goalies.NAME == "Goalies"
    assert goalies.ORDER == 3


def test_layout_shows_a_position_specific_draft_grid(walk_components):
    grid = next(node for node in walk_components(goalies.layout()) if isinstance(node, dag.AgGrid))
    assert grid.id == "g-player-grid"
    assert [column["headerName"] for column in grid.columnDefs] == ["Name", "Status"]
