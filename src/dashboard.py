"""Top-level app shell: persistent menu + multi-page routing.

Pages live under `src/pages/` and each registers itself via
`dash.register_page` (see that package's docstring for the required
per-page conventions). This module only wires the app shell together:
the persistent menu, the page container, and the landing-page redirect.
"""

from __future__ import annotations

import dash
from dash import Dash, Input, Output, callback, html

from .components.menu import build_menu
from .storage import ensure_schema, get_workspace_summary

# The id Dash's page-routing machinery uses for its internal dcc.Location.
# Exposed as a "private" attribute by Dash itself; pinned here in one place
# so a future Dash upgrade only needs to be reconciled in this one spot.
_PAGES_LOCATION_ID = getattr(dash.dash, "_ID_LOCATION", "_pages_location")


def _landing_page_path() -> str:
    """Decide which page to redirect to from "/".

    If the workspace already has imported players, land on the Data table 1
    page; otherwise land on the Import data page so the user is prompted to
    import a season's CSV export first.
    """
    # Imported lazily: these modules call `dash.register_page(...)` at import
    # time, which Dash only allows after a `Dash(use_pages=True, ...)` app has
    # been instantiated (see build_dashboard()).
    from .pages import data_table_1, import_data

    summary = get_workspace_summary()
    if summary["total_players"] > 0:
        return data_table_1.PATH
    return import_data.PATH


def build_dashboard() -> Dash:
    """Create the multi-page app: persistent menu + routed page content."""
    ensure_schema()

    app = Dash(__name__, use_pages=True, pages_folder="")

    # Importing the page modules triggers their `dash.register_page(...)` calls.
    # This must happen after the Dash(use_pages=True) app above is created.
    from .pages import data_table_1, import_data  # noqa: F401  (side-effect import)

    app.layout = html.Div(
        style={"padding": "24px", "fontFamily": "sans-serif"},
        children=[
            html.H2("NHL Auction Draft Wizard"),
            build_menu(),
            dash.page_container,
        ],
    )

    @callback(
        Output(_PAGES_LOCATION_ID, "pathname"),
        Input(_PAGES_LOCATION_ID, "pathname"),
        prevent_initial_call=False,
    )
    def redirect_root(pathname):
        if pathname in ("/", ""):
            return _landing_page_path()
        return dash.no_update

    return app
