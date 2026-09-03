"""Selected player graphs page for the shared highlighted player's history."""

from __future__ import annotations

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from ..storage import get_player_stat_history, get_selected_player

PATH = "/selected-player-graphs"
NAME = "Selected player graphs"
ORDER = 6
REFRESH_INTERVAL_ID = "selected-player-graphs-refresh"
PLAYER_NAME_ID = "selected-player-graphs-player-name"
GRAPH_CONTAINER_ID = "selected-player-graphs-container"
_ACTUAL_COLOR = "#1f77b4"
_PROJECTED_COLOR = "#ff7f0e"


def _history_by_year(player_id: int) -> pd.DataFrame:
    """Pivot one player's long-format stat history into one row per season."""
    history = get_player_stat_history(player_id)
    if history.empty:
        return pd.DataFrame()

    table = history.pivot(index=["year", "stats_type"], columns="stat_name", values="stat_value")
    return table.reset_index().sort_values(["year", "stats_type"], kind="stable")


def _metric_values(table: pd.DataFrame, stat_name: str) -> tuple[pd.Series, pd.Series]:
    """Return actual and projected values for a stored statistic by season."""
    actual = table[table["stats_type"] == "actual"].set_index("year")
    projected = table[table["stats_type"] == "projected"].set_index("year")
    return (
        pd.to_numeric(actual.get(stat_name, pd.Series(dtype=float)), errors="coerce"),
        pd.to_numeric(projected.get(stat_name, pd.Series(dtype=float)), errors="coerce"),
    )


def _derived_metric_values(
    table: pd.DataFrame, numerator: str, denominator: str, *, multiplier: float = 1.0
) -> tuple[pd.Series, pd.Series]:
    """Return a rate calculated from imported numerator and denominator stats."""
    actual_numerator, projected_numerator = _metric_values(table, numerator)
    actual_denominator, projected_denominator = _metric_values(table, denominator)
    return (
        actual_numerator.div(actual_denominator.where(actual_denominator != 0)).mul(multiplier),
        projected_numerator.div(projected_denominator.where(projected_denominator != 0)).mul(multiplier),
    )


def _build_chart(
    title: str,
    actual: pd.Series,
    projected: pd.Series | None = None,
    *,
    yaxis_title: str | None = None,
) -> dcc.Graph:
    """Build one annual actual bar chart with an optional projected line."""
    years = sorted(set(actual.index).union(projected.index if projected is not None else []))
    figure = go.Figure(
        go.Bar(
            name="Actual",
            x=years,
            y=actual.reindex(years),
            marker_color=_ACTUAL_COLOR,
        )
    )
    if projected is not None:
        figure.add_trace(
            go.Scatter(
                name="Projected",
                x=years,
                y=projected.reindex(years),
                mode="lines+markers",
                line={"color": _PROJECTED_COLOR, "width": 3},
            )
        )
    figure.update_layout(
        title=title,
        barmode="group",
        margin={"l": 50, "r": 20, "t": 50, "b": 45},
        legend={"orientation": "h", "y": 1.12},
    )
    figure.update_xaxes(title="Year", type="category")
    figure.update_yaxes(title=yaxis_title)
    return dcc.Graph(figure=figure, config={"displayModeBar": False}, className="selected-player-graph")


def build_player_graphs(player: dict[str, int | str] | None = None) -> list[dcc.Graph]:
    """Build the position-appropriate annual charts for the highlighted player."""
    player = get_selected_player() if player is None else player
    if player is None:
        return []

    table = _history_by_year(int(player["id"]))
    if table.empty:
        return []

    charts = []
    actual, projected = _metric_values(table, "FP_AVG")
    charts.append(_build_chart("AVG Performance", actual, projected, yaxis_title="Fantasy points average"))

    if player["position"] in {"F", "D"}:
        actual, _ = _metric_values(table, "GP")
        charts.append(_build_chart("Health", actual, yaxis_title="Games played"))
        actual, projected = _metric_values(table, "PTS")
        charts.append(_build_chart("Points", actual, projected, yaxis_title="Points"))
        actual, projected = _metric_values(table, "STP")
        charts.append(_build_chart("Special Teams Points", actual, projected, yaxis_title="Points"))
        actual, _ = _metric_values(table, "HIT")
        charts.append(_build_chart("Hits", actual, yaxis_title="Hits"))
        actual, _ = _metric_values(table, "BLK")
        charts.append(_build_chart("Blocks", actual, yaxis_title="Blocks"))
        actual, _ = _derived_metric_values(table, "TTOI", "GP", multiplier=1 / 60)
        charts.append(_build_chart("Time on Ice", actual, yaxis_title="Minutes per game"))
        actual, _ = _derived_metric_values(table, "SOG", "GP")
        charts.append(_build_chart("Shots on Goal per Game", actual, yaxis_title="Shots per game"))

    if player["position"] == "F":
        actual, projected = _derived_metric_values(table, "G", "SOG", multiplier=100)
        charts.append(_build_chart("Shooting Percentage", actual, projected, yaxis_title="Percent"))
        actual, projected = _metric_values(table, "G")
        charts.append(_build_chart("Goals", actual, projected, yaxis_title="Goals"))
        actual, projected = _metric_values(table, "A")
        charts.append(_build_chart("Assists", actual, projected, yaxis_title="Assists"))

    if player["position"] == "G":
        actual, projected = _metric_values(table, "GS")
        charts.append(_build_chart("Game Starts", actual, projected, yaxis_title="Games started"))
        actual, projected = _metric_values(table, "_12")
        charts.append(_build_chart("Win Percentage", actual, projected, yaxis_title="Win percentage"))
        actual, projected = _metric_values(table, "SVP")
        charts.append(_build_chart("Save Percentage", actual, projected, yaxis_title="Save percentage"))

    return charts


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
            html.Div(
                build_player_graphs(),
                id=GRAPH_CONTAINER_ID,
                className="selected-player-graphs",
            ),
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


@callback(
    Output(GRAPH_CONTAINER_ID, "children"),
    Input(REFRESH_INTERVAL_ID, "n_intervals"),
)
def refresh_selected_player_graphs(_n_intervals: int) -> list[dcc.Graph]:
    """Refresh graphs after another page changes the shared player selection."""
    return build_player_graphs()
