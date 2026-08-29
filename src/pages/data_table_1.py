"""Page 1 - "Data table 1": placeholder for the future data-analysis page.

This page has no functionality yet. It exists so the menu, routing, and
documentation structure for future analysis features are already in place.
See `docs/pages/data-table-1.md` for the current status of this page.
"""

from __future__ import annotations

import dash
from dash import html

PATH = "/data-table-1"
NAME = "Data table 1"
ORDER = 1

dash.register_page(__name__, path=PATH, name=NAME, order=ORDER)


def layout(**_kwargs):
    """Placeholder layout. Replace with real content when this page is implemented."""
    return html.Div(
        style={"maxWidth": "760px"},
        children=[
            html.H2("Data table 1"),
            html.P(
                "This page is a placeholder for the future data-analysis feature "
                "(historical projected-vs-actual comparisons across seasons)."
            ),
            html.P("No functionality is implemented here yet.", style={"fontStyle": "italic", "color": "#555"}),
        ],
    )
