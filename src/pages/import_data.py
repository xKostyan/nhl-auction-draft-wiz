"""Page 0 - "Import data": upload the yearly CSV export and clear the workspace.

This page owns the existing import / clear-workspace capability. See
`docs/pages/import-data.md` for the user-facing description of this page.
"""

from __future__ import annotations

import dash
import dash_ag_grid as dag
from dash import Input, Output, State, callback, ctx, dcc, html

from ..data_loader import parse_uploaded_csv
from ..storage import (
    clear_workspace,
    get_players_for_grid,
    get_workspace_summary,
    import_yearly_dataset,
)

PATH = "/import-data"
NAME = "Import data"
ORDER = 0

dash.register_page(__name__, path=PATH, name=NAME, order=ORDER)

UPLOAD_STYLE = {
    "width": "100%",
    "height": "56px",
    "lineHeight": "56px",
    "borderWidth": "1px",
    "borderStyle": "dashed",
    "borderRadius": "6px",
    "textAlign": "center",
}

UPLOAD_FIELDS = [
    ("upload-players", "Players CSV"),
    ("upload-forwards", "Forwards stats CSV"),
    ("upload-defense", "Defencemen stats CSV"),
    ("upload-goalies", "Goalies stats CSV"),
]


def _upload_control(upload_id: str, label: str) -> html.Div:
    return html.Div(
        [
            html.Label(label),
            dcc.Upload(
                id=upload_id,
                children=html.Div(["Drag and drop or ", html.A("select a CSV file")]),
                style=UPLOAD_STYLE,
                multiple=False,
                accept=".csv",
            ),
            html.Div(id=f"{upload_id}-filename", style={"fontSize": "12px", "color": "#555", "minHeight": "18px"}),
        ],
        style={"marginBottom": "12px"},
    )


def _initial_status_message() -> str:
    summary = get_workspace_summary()
    if summary["total_players"] == 0:
        return "Workspace is empty. Import the players/forwards/defencemen/goalies CSV files to begin."
    return f"Workspace has {summary['total_players']} players imported for season {summary['current_season']}."


def handle_workspace_action(
    triggered_id: str | None,
    players_contents: str | None,
    forwards_contents: str | None,
    defense_contents: str | None,
    goalies_contents: str | None,
) -> tuple[str, list[dict]]:
    """Run the import/clear workspace action and return (status message, grid rows).

    Kept free of Dash callback machinery so it can be unit tested directly.
    """
    if triggered_id == "clear-button":
        clear_workspace()
        return (
            "Workspace cleared. Import a new season's CSV export to continue.",
            get_players_for_grid().to_dict("records"),
        )

    if triggered_id == "import-button":
        missing = [
            label
            for label, contents in (
                ("players", players_contents),
                ("forwards", forwards_contents),
                ("defencemen", defense_contents),
                ("goalies", goalies_contents),
            )
            if not contents
        ]
        if missing:
            message = f"Please select all four CSV files before importing. Missing: {', '.join(missing)}."
            return message, get_players_for_grid().to_dict("records")

        try:
            result = import_yearly_dataset(
                parse_uploaded_csv(players_contents),
                parse_uploaded_csv(forwards_contents),
                parse_uploaded_csv(defense_contents),
                parse_uploaded_csv(goalies_contents),
            )
        except ValueError as exc:
            return f"Import failed: {exc}", get_players_for_grid().to_dict("records")

        message = f"Imported {result['players_imported']} players for season {result['year']}."
        return message, get_players_for_grid().to_dict("records")

    return _initial_status_message(), get_players_for_grid().to_dict("records")


def layout(**_kwargs):
    """Build the page layout. A function (not a static value) so the status
    message and grid reflect the current workspace state on every page visit."""
    return html.Div(
        style={"maxWidth": "760px"},
        children=[
            html.H2("Import data"),
            html.P(
                "Import the yearly players / forwards / defencemen / goalies CSV export to build the "
                "local draft workspace, or clear the workspace to prepare for a new season."
            ),
            *[_upload_control(upload_id, label) for upload_id, label in UPLOAD_FIELDS],
            html.Div(
                [
                    html.Button("Import season data", id="import-button", n_clicks=0, style={"marginRight": "12px"}),
                    html.Button("Clear workspace", id="clear-button", n_clicks=0),
                ],
                style={"margin": "16px 0"},
            ),
            html.Div(id="workspace-status", children=_initial_status_message(), style={"marginBottom": "16px", "fontWeight": "bold"}),
            dag.AgGrid(
                id="player-grid",
                rowData=get_players_for_grid().to_dict("records"),
                columnDefs=[
                    {"field": "id"},
                    {"field": "name"},
                    {"field": "position"},
                    {"field": "status"},
                    {"field": "current_season"},
                ],
                defaultColDef={"sortable": True, "resizable": True},
                dashGridOptions={"pagination": True, "paginationPageSize": 25},
                style={"height": "440px", "width": "100%"},
            ),
        ],
    )


for _upload_id, _ in UPLOAD_FIELDS:

    def _make_filename_callback(component_id: str):
        @callback(
            Output(f"{component_id}-filename", "children"),
            Input(component_id, "filename"),
            prevent_initial_call=True,
        )
        def show_filename(filename, _component_id=component_id):
            return f"Selected: {filename}" if filename else ""

        return show_filename

    _make_filename_callback(_upload_id)


@callback(
    Output("workspace-status", "children"),
    Output("player-grid", "rowData"),
    Input("import-button", "n_clicks"),
    Input("clear-button", "n_clicks"),
    State("upload-players", "contents"),
    State("upload-forwards", "contents"),
    State("upload-defense", "contents"),
    State("upload-goalies", "contents"),
    prevent_initial_call=True,
)
def handle_workspace_actions(
    _import_clicks,
    _clear_clicks,
    players_contents,
    forwards_contents,
    defense_contents,
    goalies_contents,
):
    return handle_workspace_action(
        ctx.triggered_id,
        players_contents,
        forwards_contents,
        defense_contents,
        goalies_contents,
    )
