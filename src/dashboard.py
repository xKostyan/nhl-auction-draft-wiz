from __future__ import annotations

from dash import Dash, Input, Output, State, dcc, html
import dash_ag_grid as dag
import plotly.express as px

from .data_loader import load_player_data
from .storage import (
    clear_workspace,
    ensure_schema,
    get_players_for_grid,
    get_workspace_summary,
    import_yearly_dataset,
    set_player_status,
)


def build_dashboard() -> Dash:
    """Create the app and wire the yearly import / workspace-state experience."""
    ensure_schema()
    sample_data = load_player_data()
    position_options = [{"label": label, "value": value} for label, value in [("All", "all"), ("F", "F"), ("D", "D"), ("G", "G")]]
    status_options = [
        {"label": "Available", "value": "available"},
        {"label": "Drafted", "value": "drafted"},
        {"label": "Keeper", "value": "keeper"},
        {"label": "Unavailable", "value": "unavailable"},
    ]

    app = Dash(__name__)
    app.layout = html.Div(
        style={"padding": "24px", "fontFamily": "sans-serif"},
        children=[
            html.H2("NHL Auction Draft Wizard"),
            html.Div(
                [
                    html.Label("Import year"),
                    dcc.Input(id="import-year", type="number", value=2025, min=2020, max=2100, style={"marginLeft": "12px"}),
                    html.Button("Import yearly CSV dataset", id="import-button", n_clicks=0, style={"marginLeft": "12px"}),
                    html.Button("Clear workspace", id="clear-button", n_clicks=0, style={"marginLeft": "12px"}),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": "16px"},
            ),
            html.Div(id="workspace-status", style={"marginBottom": "16px"}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Filter by status"),
                            dcc.Dropdown(
                                id="status-filter",
                                options=[{"label": "All", "value": "all"}] + status_options,
                                value="all",
                                clearable=False,
                                style={"minWidth": "180px"},
                            ),
                        ],
                        style={"width": "220px", "marginRight": "20px"},
                    ),
                    html.Div(
                        [
                            html.Label("Player"),
                            dcc.Dropdown(id="player-status-selector", options=[], clearable=False, style={"minWidth": "220px"}),
                        ],
                        style={"width": "260px", "marginRight": "20px"},
                    ),
                    html.Div(
                        [
                            html.Label("Set as"),
                            dcc.Dropdown(id="player-status-value", options=status_options, value="drafted", clearable=False, style={"minWidth": "180px"}),
                        ],
                        style={"width": "220px", "marginRight": "20px"},
                    ),
                    html.Button("Apply status", id="apply-status-button", n_clicks=0, style={"alignSelf": "end"}),
                ],
                style={"display": "flex", "alignItems": "end", "marginBottom": "16px"},
            ),
            html.Div(
                [
                    html.Label("Position"),
                    dcc.Dropdown(
                        id="position-selector",
                        options=position_options,
                        value="all",
                        clearable=False,
                        style={"minWidth": "160px"},
                    ),
                ],
                style={"width": "220px", "marginBottom": "16px"},
            ),
            dag.AgGrid(
                id="player-grid",
                rowData=get_players_for_grid().to_dict("records"),
                columnDefs=[
                    {"field": "id", "filter": True},
                    {"field": "name", "filter": True},
                    {"field": "position", "filter": True},
                    {"field": "selected", "filter": True},
                    {"field": "status", "filter": True},
                    {"field": "notes", "filter": True},
                    {"field": "imported_year", "filter": True},
                ],
                defaultColDef={"sortable": True, "resizable": True},
                dashGridOptions={"pagination": True, "paginationPageSize": 25},
                style={"height": "440px", "width": "100%"},
            ),
            dcc.Graph(id="stats-chart", style={"marginTop": "20px"}),
        ],
    )

    @app.callback(
        Output("workspace-status", "children"),
        Output("player-grid", "rowData"),
        Output("player-status-selector", "options"),
        Input("import-button", "n_clicks"),
        Input("clear-button", "n_clicks"),
        Input("apply-status-button", "n_clicks"),
        Input("status-filter", "value"),
        Input("position-selector", "value"),
        State("import-year", "value"),
        State("player-status-selector", "value"),
        State("player-status-value", "value"),
    )
    def refresh_dashboard(import_clicks, clear_clicks, apply_clicks, status_filter, position_filter, import_year, player_id, new_status):
        rows = get_players_for_grid()
        message = "Workspace ready."
        ctx = app.callback_context
        triggered_id = ctx.triggered_id if ctx.triggered else None

        if triggered_id == "import-button":
            year = int(import_year or 2025)
            import_yearly_dataset(year)
            rows = get_players_for_grid()
            summary = get_workspace_summary()
            message = f"Imported {summary['total_players']} players for year {year}."
        elif triggered_id == "clear-button":
            clear_workspace()
            rows = get_players_for_grid()
            message = "Workspace cleared. Import a new yearly dataset to continue."
        elif triggered_id == "apply-status-button":
            if player_id is not None:
                set_player_status(int(player_id), new_status)
                rows = get_players_for_grid()
                summary = get_workspace_summary()
                message = f"Updated player {player_id} to {new_status}. Workspace now contains {summary['total_players']} players."
            else:
                message = "Select a player before applying a status."

        if status_filter != "all":
            rows = rows[rows["status"] == status_filter]
        if position_filter != "all":
            rows = rows[rows["position"] == position_filter]

        options = build_player_options(rows)
        return message, rows.to_dict("records"), options

    @app.callback(
        Output("stats-chart", "figure"),
        Input("position-selector", "value"),
    )
    def update_chart(position: str):
        if position == "all":
            chart_df = sample_data["forwards"].copy()
            chart_df = chart_df[chart_df["stats_type"] == "projected"].head(10)
            title = "Projected forward FP average"
        else:
            stat_key = {"F": "forwards", "D": "defense", "G": "goalies"}[position]
            chart_df = sample_data[stat_key].copy()
            chart_df = chart_df[chart_df["stats_type"] == "projected"].head(10)
            title = f"Projected {position} player FP average"

        if chart_df.empty:
            return px.bar(title=f"No projected data for {position}")

        return px.bar(chart_df, x="id", y="FP_AVG", title=title, color="id")

    def build_player_options(filtered_rows=None):
        rows = filtered_rows if filtered_rows is not None else get_players_for_grid()
        return [{"label": f"{row['name']} ({row['position']})", "value": str(row["id"])} for _, row in rows.iterrows()]

    return app
