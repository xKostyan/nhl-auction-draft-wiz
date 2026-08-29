import base64

from dash import dcc, html

from src.data_loader import load_players, load_stats
from src.dashboard import build_dashboard, handle_workspace_action
from src.storage import clear_workspace, configure_storage, get_workspace_summary


def _csv_data_url(df) -> str:
    encoded = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode()
    return f"data:text/csv;base64,{encoded}"


def _collect_component_ids(component) -> set[str]:
    ids: set[str] = set()
    component_id = getattr(component, "id", None)
    if isinstance(component_id, str):
        ids.add(component_id)

    children = getattr(component, "children", None)
    if children is None:
        return ids
    if isinstance(children, (list, tuple)):
        for child in children:
            ids |= _collect_component_ids(child)
    elif hasattr(children, "id") or hasattr(children, "children"):
        ids |= _collect_component_ids(children)
    return ids


def test_dashboard_layout_only_exposes_import_and_clear_controls(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    app = build_dashboard()
    ids = _collect_component_ids(app.layout)

    for expected_id in (
        "upload-players",
        "upload-forwards",
        "upload-defense",
        "upload-goalies",
        "import-button",
        "clear-button",
        "workspace-status",
        "player-grid",
    ):
        assert expected_id in ids

    def _walk(component):
        yield component
        children = getattr(component, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                yield from _walk(child)
        elif children is not None and (hasattr(children, "id") or hasattr(children, "children")):
            yield from _walk(children)

    assert not any(isinstance(node, dcc.Graph) for node in _walk(app.layout))


def test_import_action_requires_all_four_files(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    message, rows = handle_workspace_action("import-button", None, None, None, None)

    assert "Please select all four CSV files" in message
    assert rows == []


def test_import_action_imports_uploaded_csv_files(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    message, rows = handle_workspace_action(
        "import-button",
        _csv_data_url(load_players()),
        _csv_data_url(load_stats("F")),
        _csv_data_url(load_stats("D")),
        _csv_data_url(load_stats("G")),
    )

    assert message.startswith("Imported")
    assert len(rows) > 0
    summary = get_workspace_summary()
    assert summary["total_players"] == len(rows)


def test_clear_action_resets_workspace(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    handle_workspace_action(
        "import-button",
        _csv_data_url(load_players()),
        _csv_data_url(load_stats("F")),
        _csv_data_url(load_stats("D")),
        _csv_data_url(load_stats("G")),
    )

    message, rows = handle_workspace_action("clear-button", None, None, None, None)

    assert "cleared" in message.lower()
    assert rows == []
    assert get_workspace_summary()["total_players"] == 0
