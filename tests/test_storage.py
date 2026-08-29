import pandas as pd
import pytest

from src.storage import (
    clear_workspace,
    configure_storage,
    detect_draft_year,
    get_players_for_grid,
    get_workspace_summary,
    import_yearly_dataset,
)


def test_import_uses_bundled_sample_data_by_default(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    result = import_yearly_dataset()
    assert result["players_imported"] > 0
    assert result["year"] > 0

    rows = get_players_for_grid()
    assert not rows.empty
    assert set(["id", "name", "position", "status", "imported_year"]).issubset(rows.columns)
    assert rows["status"].isin(["available"]).all()

    summary = get_workspace_summary()
    assert summary["total_players"] == result["players_imported"]
    assert summary["current_year"] == result["year"]
    assert summary["last_imported_at"]


def test_import_only_keeps_the_detected_draft_year(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    result = import_yearly_dataset()
    rows = get_players_for_grid()
    assert (rows["imported_year"] == result["year"]).all()


def test_clear_workspace_resets_to_empty_state(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    import_yearly_dataset()
    assert not get_players_for_grid().empty

    clear_workspace()
    assert get_players_for_grid().empty
    summary = get_workspace_summary()
    assert summary["total_players"] == 0
    assert summary["current_year"] == 0
    assert summary["last_imported_at"] == ""


def test_detect_draft_year_picks_the_season_with_no_actual_data():
    frame = pd.DataFrame(
        {
            "id": [1, 1, 1, 1],
            "year": [2023, 2023, 2024, 2024],
            "stats_type": ["projected", "actual", "projected", "actual"],
            "FP": [10.0, 12.0, 8.0, None],
        }
    )
    assert detect_draft_year(frame) == 2024


def test_detect_draft_year_falls_back_to_max_year_when_all_have_actuals():
    frame = pd.DataFrame(
        {
            "id": [1, 1],
            "year": [2023, 2024],
            "stats_type": ["actual", "actual"],
            "FP": [10.0, 12.0],
        }
    )
    assert detect_draft_year(frame) == 2024


def test_detect_draft_year_raises_without_any_year_data():
    with pytest.raises(ValueError):
        detect_draft_year(pd.DataFrame())


def test_import_raises_when_required_columns_are_missing(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    bad_players = pd.DataFrame({"id": [1], "name": ["Test Player"]})  # missing "position"
    with pytest.raises(ValueError):
        import_yearly_dataset(players_df=bad_players)
