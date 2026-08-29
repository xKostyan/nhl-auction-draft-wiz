"""Tests for the "Import data" page (`src/pages/import_data.py`, path `/import-data`).

See `docs/pages/import-data.md` for the page's user-facing behavior.
"""

from dash import dcc

from src.data_loader import load_players, load_stats
from src.pages import import_data
from src.storage import clear_workspace, configure_storage, get_workspace_summary


def test_page_is_registered_at_the_expected_path_and_order():
    assert import_data.PATH == "/import-data"
    assert import_data.NAME == "Import data"
    assert import_data.ORDER == 0


def test_layout_exposes_upload_import_and_clear_controls(tmp_path, collect_component_ids, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    layout = import_data.layout()
    ids = collect_component_ids(layout)

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

    # This page has no charts/graphs yet.
    assert not any(isinstance(node, dcc.Graph) for node in walk_components(layout))


def test_import_action_requires_all_four_files(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    message, rows = import_data.handle_workspace_action("import-button", None, None, None, None)

    assert "Please select all four CSV files" in message
    assert rows == []


def test_import_action_imports_uploaded_csv_files(tmp_path, csv_data_url):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    message, rows = import_data.handle_workspace_action(
        "import-button",
        csv_data_url(load_players()),
        csv_data_url(load_stats("F")),
        csv_data_url(load_stats("D")),
        csv_data_url(load_stats("G")),
    )

    assert message.startswith("Imported")
    assert len(rows) > 0
    summary = get_workspace_summary()
    assert summary["total_players"] == len(rows)


def test_clear_action_resets_workspace(tmp_path, csv_data_url):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    import_data.handle_workspace_action(
        "import-button",
        csv_data_url(load_players()),
        csv_data_url(load_stats("F")),
        csv_data_url(load_stats("D")),
        csv_data_url(load_stats("G")),
    )

    message, rows = import_data.handle_workspace_action("clear-button", None, None, None, None)

    assert "cleared" in message.lower()
    assert rows == []
    assert get_workspace_summary()["total_players"] == 0
