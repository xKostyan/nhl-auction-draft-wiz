"""Selected player graphs page: the shared visual surface for future charts."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, dcc, html

from ..storage import get_selected_player

PATH = "/selected-player-graphs"
NAME = "Selected player graphs"
ORDER = 6
REFRESH_INTERVAL_ID = "selected-player-graphs-refresh"
PLAYER_NAME_ID = "selected-player-graphs-player-name"


def get_selected_player_name() -> str:
    """Return the selected player's name, or the initial empty-workspace message."""
    player = get_selected_player()
    return str(player["name"]) if player is not None else "No player highlighted."


def layout(**_kwargs):
    """Build the persistent graph surface, refreshed from the shared workspace selection."""
    return html.Div(
        className="selected-player-graphs-page",
        children=[
            html.H2("Selected player graphs"),
            dcc.Interval(id=REFRESH_INTERVAL_ID, interval=1_000, n_intervals=0),
            html.H3(get_selected_player_name(), id=PLAYER_NAME_ID),
        ],
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


@callback(
    Output(PLAYER_NAME_ID, "children"),
    Input(REFRESH_INTERVAL_ID, "n_intervals"),
)
def refresh_selected_player_name(_n_intervals: int) -> str:
    """Refresh the dedicated tab after any open player table changes selection."""
    return get_selected_player_name()
