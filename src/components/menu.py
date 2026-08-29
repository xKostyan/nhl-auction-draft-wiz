"""Persistent top navigation menu, shown on every page.

The menu is a single button that toggles a dropdown list of the registered
pages (in `dash.page_registry` order). Keep this module free of page-specific
logic; add new pages by registering them in `src/pages/` and they will appear
here automatically, ordered by their `order` value.
"""

from __future__ import annotations

import dash
from dash import Input, Output, callback, html

MENU_TOGGLE_ID = "app-menu-toggle"
MENU_PANEL_ID = "app-menu-panel"

_PANEL_HIDDEN_STYLE = {"display": "none"}
_PANEL_VISIBLE_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "position": "absolute",
    "top": "100%",
    "left": 0,
    "backgroundColor": "#ffffff",
    "border": "1px solid #ccc",
    "borderRadius": "4px",
    "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)",
    "minWidth": "220px",
    "zIndex": 1000,
}


def build_menu() -> html.Div:
    """Build the persistent menu button + dropdown of registered pages."""
    pages = sorted(dash.page_registry.values(), key=lambda page: page.get("order", 0))
    links = [
        html.A(
            f"{index + 1} - {page['name']}",
            href=page["relative_path"],
            style={"padding": "8px 16px", "textDecoration": "none", "color": "#222"},
        )
        for index, page in enumerate(pages)
    ]

    return html.Div(
        style={"position": "relative", "marginBottom": "20px"},
        children=[
            html.Button("☰ Menu", id=MENU_TOGGLE_ID, n_clicks=0),
            html.Div(id=MENU_PANEL_ID, children=links, style=_PANEL_HIDDEN_STYLE),
        ],
    )


@callback(
    Output(MENU_PANEL_ID, "style"),
    Input(MENU_TOGGLE_ID, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_menu(n_clicks: int):
    """Show the dropdown on odd click counts, hide it on even ones."""
    if n_clicks % 2 == 1:
        return _PANEL_VISIBLE_STYLE
    return _PANEL_HIDDEN_STYLE
