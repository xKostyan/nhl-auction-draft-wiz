"""Tests for the top-level app shell: persistent menu, page registry, and the
landing-page redirect on "/" (see `src/dashboard.py`, `src/components/menu.py`).

Individual page content is tested under `tests/pages/<page>/`.
"""

from pathlib import Path

import dash

from src.components.menu import (
    MENU_CONTAINER_ID,
    _PANEL_HIDDEN_STYLE,
    _PANEL_VISIBLE_STYLE,
    toggle_menu,
)
from src.dashboard import _landing_page_path, build_dashboard
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_all_pages_are_registered_in_menu_order():
    pages = sorted(dash.page_registry.values(), key=lambda page: page.get("order", 0))
    paths_in_order = [page["relative_path"] for page in pages]
    assert paths_in_order == [
        "/import-data",
        "/forwards",
        "/defencemen",
        "/goalies",
        "/my-team",
        "/player-stats-table",
        "/selected-player-graphs",
    ]


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
    assert dash_app.layout.className == "app-shell"
    assert len(dash_app.layout.children) == 2
    assert dash_app.layout.children[0].children[0].id == "app-menu-toggle"
    assert dash_app.layout.children[0].id == MENU_CONTAINER_ID
    assert dash_app.layout.children[-1].className == "page-container"


def test_menu_toggles_using_its_current_visibility_state():
    assert toggle_menu(1, _PANEL_HIDDEN_STYLE) == _PANEL_VISIBLE_STYLE
    assert toggle_menu(2, _PANEL_VISIBLE_STYLE) == _PANEL_HIDDEN_STYLE


def test_menu_asset_closes_an_open_menu_after_an_outside_left_click():
    script = (Path(__file__).parents[2] / "src" / "assets" / "menu.js").read_text()

    assert 'document.addEventListener("mousedown"' in script
    assert 'menu.contains(event.target)' in script
    assert 'window.dash_clientside.set_props("app-menu-panel"' in script


def test_landing_page_is_import_data_when_workspace_is_empty(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    assert _landing_page_path() == "/import-data"


def test_landing_page_is_my_team_when_workspace_has_players(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    assert _landing_page_path() == "/my-team"
