from src.storage import (
    clear_workspace,
    configure_storage,
    get_players_for_grid,
    import_yearly_dataset,
    set_player_status,
)


def test_import_and_clear_workspace(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    count = import_yearly_dataset(2025)
    assert count > 0

    rows = get_players_for_grid()
    assert "status" in rows.columns
    assert rows["status"].notna().all()
    assert rows["status"].isin(["available"]).all()

    target_id = int(rows.iloc[0]["id"])
    set_player_status(target_id, "keeper", "kept")
    assert get_players_for_grid().iloc[0]["status"] == "keeper"

    clear_workspace()
    assert get_players_for_grid().empty
