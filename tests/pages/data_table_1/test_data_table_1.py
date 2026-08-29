"""Tests for the "Data table 1" page (`src/pages/data_table_1.py`, path `/data-table-1`).

This page is currently a placeholder for a future data-analysis feature. See
`docs/pages/data-table-1.md` for its current status.
"""

from dash import dcc

from src.pages import data_table_1


def test_page_is_registered_at_the_expected_path_and_order():
    assert data_table_1.PATH == "/data-table-1"
    assert data_table_1.NAME == "Data table 1"
    assert data_table_1.ORDER == 4


def test_layout_renders_placeholder_content_only(walk_components):
    layout = data_table_1.layout()

    text_nodes = [
        node.children
        for node in walk_components(layout)
        if isinstance(getattr(node, "children", None), str)
    ]
    assert any("placeholder" in text.lower() or "not implemented" in text.lower() or "no functionality" in text.lower() for text in text_nodes)

    # No interactive/data components should exist yet on this placeholder page.
    assert not any(isinstance(node, (dcc.Graph, dcc.Upload)) for node in walk_components(layout))
