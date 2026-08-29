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
ORDER = 4


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


# Registered here (after `layout` is defined) rather than at module import time,
# because dash.register_page() looks up `layout` from this module's namespace
# at call time if not passed explicitly — see the matching comment in
# src/pages/import_data.py for details.
dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)
