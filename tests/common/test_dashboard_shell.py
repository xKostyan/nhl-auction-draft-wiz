"""Tests for the top-level app shell: persistent menu, page registry, and the
landing-page redirect on "/" (see `src/dashboard.py`, `src/components/menu.py`).

Individual page content is tested under `tests/pages/<page>/`.
"""

import dash

from src.dashboard import _landing_page_path, build_dashboard
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_all_pages_are_registered_in_menu_order():
    pages = sorted(dash.page_registry.values(), key=lambda page: page.get("order", 0))
    paths_in_order = [page["relative_path"] for page in pages]
    assert paths_in_order == ["/import-data", "/forwards", "/defencemen", "/goalies", "/data-table-1"]


def test_every_registered_page_has_a_callable_layout():
    """Regression test: dash.register_page() silently stores layout=None if it
    is called before the module's `layout` function is defined and `layout`
    isn't passed explicitly, which renders an empty page with no error. Every
    page must register a real callable layout."""
    for module_name, page in dash.page_registry.items():
        assert callable(page.get("layout")), f"{module_name} registered without a callable layout"


def test_app_layout_contains_persistent_menu_and_page_container(dash_app, collect_component_ids):
    ids = collect_component_ids(dash_app.layout)
    assert "app-menu-toggle" in ids
    assert "app-menu-panel" in ids


def test_landing_page_is_import_data_when_workspace_is_empty(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    assert _landing_page_path() == "/import-data"


def test_landing_page_is_forwards_when_workspace_has_players(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    assert _landing_page_path() == "/forwards"
