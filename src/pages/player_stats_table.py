"""Player stats table page: inspect all stored data for one selected player."""

from __future__ import annotations

import dash
import dash_ag_grid as dag
import pandas as pd
from dash import Input, Output, callback, dcc, html

from ..storage import get_player_stat_history, get_players_for_stat_lookup

PATH = "/player-stats-table"
NAME = "Player stats table"
ORDER = 5
PLAYER_SEARCH_ID = "player-stats-player-search"
GRID_ID = "player-stats-grid"
_IDENTIFIER_COLUMNS = ["year", "stats_type"]


def get_player_options() -> list[dict[str, int | str]]:
    """Build searchable dropdown options from every player in the workspace."""
    return [
        {"label": row.name, "value": int(row.id)}
        for row in get_players_for_stat_lookup().itertuples(index=False)
    ]


def build_player_stats_table(player_id: int | None) -> tuple[list[dict], list[dict]]:
    """Return dynamic AG Grid rows and columns for one player's stored stats.

    Stat columns are derived directly from the player's long-format history.
    Their database names remain unchanged so skater and goalie schemas render
    without a page-level schema or name mapping.
    """
    column_defs = [
        {"field": "year", "headerName": "year", "type": "numericColumn"},
        {"field": "stats_type", "headerName": "stats_type"},
    ]
    if player_id is None:
        return [], column_defs

    history = get_player_stat_history(player_id)
    if history.empty:
        return [], column_defs

    stat_names = sorted(history["stat_name"].unique().tolist())
    table = (
        history.pivot(index=_IDENTIFIER_COLUMNS, columns="stat_name", values="stat_value")
        .reindex(columns=stat_names)
        .reset_index()
        .sort_values(_IDENTIFIER_COLUMNS, kind="stable")
    )
    table.columns.name = None
    rows = table.where(pd.notna(table), None).to_dict("records")
    column_defs.extend(
        {"field": stat_name, "headerName": stat_name, "type": "numericColumn"}
        for stat_name in stat_names
    )
    return rows, column_defs


def layout(**_kwargs):
    """Build the player lookup and initially empty, schema-free stats grid."""
    rows, column_defs = build_player_stats_table(None)
    return html.Div(
        className="player-stats-page",
        children=[
            html.H2("Player stats table"),
            html.P("Search all imported players to view every stored stat by year and data type."),
            dcc.Dropdown(
                id=PLAYER_SEARCH_ID,
                options=get_player_options(),
                placeholder="Search players...",
                searchable=True,
                clearable=True,
                className="player-search",
            ),
            dag.AgGrid(
                id=GRID_ID,
                rowData=rows,
                columnDefs=column_defs,
                defaultColDef={"resizable": True, "sortable": True},
                dashGridOptions={"pagination": True, "paginationPageSize": 25},
                style={"flex": "1 1 0", "minHeight": 0, "width": "100%"},
            ),
        ],
    )


dash.register_page(__name__, path=PATH, name=NAME, order=ORDER, layout=layout)


@callback(
    Output(GRID_ID, "rowData"),
    Output(GRID_ID, "columnDefs"),
    Input(PLAYER_SEARCH_ID, "value"),
)
def update_player_stats_table(player_id: int | None) -> tuple[list[dict], list[dict]]:
    """Regenerate the table whenever the selected player changes."""
    return build_player_stats_table(player_id)
