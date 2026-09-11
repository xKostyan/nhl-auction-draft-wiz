import sqlite3

import pandas as pd
import pytest

import src.storage as storage
from src.data_loader import load_stats
from src.storage import (
    clear_workspace,
    configure_storage,
    detect_draft_year,
    get_available_stat_years,
    get_draft_budget,
    get_target_total_fp,
    get_player_stat_history,
    get_selected_player,
    get_players_for_position_grid,
    get_players_for_grid,
    get_workspace_summary,
    import_keeper_prices,
    import_yearly_dataset,
    set_player_drafted,
    set_draft_budget,
    set_target_total_fp,
    set_player_notes,
    set_player_auction_price,
    set_player_on_my_team,
    set_player_price,
    set_player_tags,
    set_selected_player,
    PlayerPriceRequiredError,
)


def test_import_uses_bundled_sample_data_by_default(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    result = import_yearly_dataset()
    assert result["players_imported"] > 0
    assert result["year"] > 0
    assert result["stat_rows_imported"] > 0

    rows = get_players_for_grid()
    assert not rows.empty
    assert set(["id", "name", "position", "price", "auction_price", "status", "current_season"]).issubset(rows.columns)
    assert rows["price"].isna().all()
    assert rows["auction_price"].isna().all()
    assert rows["status"].isin(["available"]).all()

    summary = get_workspace_summary()
    assert summary["total_players"] == result["players_imported"]
    assert summary["total_stat_rows"] == result["stat_rows_imported"]
    assert summary["current_season"] == result["year"]
    assert summary["last_imported_at"]


def test_players_are_tagged_with_the_detected_current_season(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    result = import_yearly_dataset()
    rows = get_players_for_grid()
    assert (rows["current_season"] == result["year"]).all()


def test_import_stores_full_multi_year_projected_and_actual_history(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    import_yearly_dataset()

    years = get_available_stat_years()
    # The bundled sample data spans multiple seasons; all of them should be retained,
    # not just the detected upcoming draft season.
    assert len(years) > 1

    rows = get_players_for_grid()
    # Pick the player with the richest history (a long-tenured veteran) rather than
    # an arbitrary player, since some players only have data for a single season.
    player_ids = rows["id"].astype(int).tolist()
    histories = {pid: get_player_stat_history(pid) for pid in player_ids}
    richest_player_id = max(histories, key=lambda pid: len(histories[pid]))
    history = histories[richest_player_id]

    assert not history.empty
    assert set(["year", "stats_type", "stat_name", "stat_value"]).issubset(history.columns)
    assert set(history["year"].unique()).issubset(set(years))
    assert set(history["stats_type"].unique()).issubset({"projected", "actual"})
    # A player with rich history should have projected data across more than one year.
    assert history[history["stats_type"] == "projected"]["year"].nunique() > 1


def test_upcoming_season_has_only_projected_history(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    result = import_yearly_dataset()
    draft_season = result["year"]

    rows = get_players_for_grid()
    player_ids = rows["id"].astype(int).tolist()
    # Find a player that actually has draft-season data (some players have none
    # for the upcoming season, e.g. projected to not play).
    season_history = pd.DataFrame()
    for player_id in player_ids:
        history = get_player_stat_history(player_id)
        season_history = history[history["year"] == draft_season]
        if not season_history.empty:
            break

    assert not season_history.empty
    assert set(season_history["stats_type"].unique()) == {"projected"}


def test_clear_workspace_resets_to_empty_state(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    import_yearly_dataset()
    assert not get_players_for_grid().empty

    clear_workspace()
    assert get_players_for_grid().empty
    assert get_available_stat_years() == []
    summary = get_workspace_summary()
    assert summary["total_players"] == 0
    assert summary["total_stat_rows"] == 0
    assert summary["current_season"] == 0
    assert summary["last_imported_at"] == ""
    assert get_selected_player() is None


def test_selected_player_is_persisted_and_reset_by_import(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = get_players_for_grid().iloc[0]

    set_selected_player(int(player["id"]))

    assert get_selected_player() == {
        "id": int(player["id"]),
        "name": player["name"],
        "position": player["position"],
    }

    import_yearly_dataset()
    assert get_selected_player() is None


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


def test_get_player_stat_history_returns_empty_frame_for_unknown_player(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    history = get_player_stat_history(-1)
    assert history.empty
    assert list(history.columns) == ["year", "stats_type", "stat_name", "stat_value"]


def test_position_grid_rows_are_filtered_and_drafted_status_is_persistent(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    forwards = get_players_for_position_grid("F")
    assert not forwards.empty
    assert list(forwards.columns) == [
        "id",
        "name",
        "position",
        "on_my_team",
        "my_team_add_error",
        "drafted",
        "price",
        "auction_price",
        "projected_tfp",
        "projected_afp",
        "actual_gp_history",
        "average_performance_history",
        "tags",
        "notes",
    ]
    assert forwards["drafted"].eq(False).all()
    assert forwards["projected_tfp"].notna().any()
    assert forwards["projected_afp"].notna().any()
    assert forwards["actual_gp_history"].map(bool).any()
    assert forwards["average_performance_history"].map(bool).all()
    assert forwards["tags"].map(lambda tags: tags == []).all()
    assert forwards["notes"].eq("").all()

    player_id = int(forwards.iloc[0]["id"])
    set_player_drafted(player_id, True)
    drafted_forwards = get_players_for_position_grid("F")
    assert drafted_forwards.loc[drafted_forwards["id"] == player_id, "drafted"].item() is True

    set_player_price(player_id, 42)
    priced_forwards = get_players_for_position_grid("F")
    assert priced_forwards.loc[priced_forwards["id"] == player_id, "price"].item() == 42
    set_player_auction_price(player_id, 37)
    priced_forwards = get_players_for_position_grid("F")
    assert priced_forwards.loc[priced_forwards["id"] == player_id, "auction_price"].item() == 37

    set_player_tags(player_id, ["PP1", "Line2", "contract", "rookie", "bounceback", "red flag"])
    tagged_forwards = get_players_for_position_grid("F")
    assert tagged_forwards.loc[tagged_forwards["id"] == player_id, "tags"].item() == [
        "Line2", "PP1", "bounceback", "contract", "red flag", "rookie"
    ]

    set_player_notes(player_id, "Top-line role; monitor injury.")
    noted_forwards = get_players_for_position_grid("F")
    assert noted_forwards.loc[noted_forwards["id"] == player_id, "notes"].item() == "Top-line role; monitor injury."

    set_player_drafted(player_id, False)
    available_forwards = get_players_for_position_grid("F")
    assert available_forwards.loc[available_forwards["id"] == player_id, "drafted"].item() is False

    set_player_on_my_team(player_id, True)
    my_team_forwards = get_players_for_position_grid("F", my_team_only=True)
    assert my_team_forwards["id"].tolist() == [player_id]
    assert my_team_forwards["on_my_team"].item() is True
    assert my_team_forwards["drafted"].item() is True

    set_player_on_my_team(player_id, False)
    assert get_players_for_position_grid("F", my_team_only=True).empty


def test_player_price_requires_a_non_negative_integer_or_blank(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = int(get_players_for_grid().iloc[0]["id"])

    set_player_price(player_id, 7)
    set_player_price(player_id, None)

    assert get_players_for_grid().loc[
        get_players_for_grid()["id"] == player_id, "price"
    ].isna().item()
    with pytest.raises(ValueError, match="non-negative integer"):
        set_player_price(player_id, -1)
    with pytest.raises(ValueError, match="non-negative integer"):
        set_player_price(player_id, 3.5)
    with pytest.raises(ValueError, match="non-negative integer"):
        set_player_auction_price(player_id, -1)


def test_player_price_is_retained_after_reconfiguring_storage(tmp_path):
    database_path = tmp_path / "draft_workspace.sqlite3"
    configure_storage(database_path)
    clear_workspace()
    import_yearly_dataset()
    player_id = int(get_players_for_grid().iloc[0]["id"])

    set_player_price(player_id, 24)
    configure_storage(database_path)

    assert get_players_for_grid().loc[
        get_players_for_grid()["id"] == player_id, "price"
    ].item() == 24


def test_import_keeper_prices_updates_matches_and_returns_unmatched_rows(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset(
        players_df=pd.DataFrame(
            {
                "id": [1, 2],
                "name": ["Test Forward", "Test Defender"],
                "position": ["F", "D"],
            }
        ),
        forward_df=pd.DataFrame({"id": [1], "year": [2026], "stats_type": ["projected"]}),
        defense_df=pd.DataFrame({"id": [2], "year": [2026], "stats_type": ["projected"]}),
        goalie_df=pd.DataFrame({"id": [3], "year": [2026], "stats_type": ["projected"]}),
    )

    result = import_keeper_prices(
        pd.DataFrame(
            [
                {"name": "  test forward ", "position": "F", "team": "ABC", "price": 18},
                {"name": "Missing Player", "position": "G", "team": "XYZ", "price": 7},
            ]
        )
    )

    assert result == {
        "prices_imported": 1,
        "unmatched_players": [
            {"name": "Missing Player", "position": "G", "team": "XYZ", "price": 7}
        ],
    }
    rows = get_players_for_grid()
    assert rows.loc[rows["name"] == "Test Forward", "price"].item() == 18
    assert rows.loc[rows["name"] == "Test Defender", "price"].isna().item()


def test_import_keeper_prices_requires_imported_players(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    with pytest.raises(ValueError, match="Import season data"):
        import_keeper_prices(
            pd.DataFrame([{"name": "Test Player", "position": "F", "team": "ABC", "price": 1}])
        )


def test_draft_budget_defaults_to_930_and_persists(tmp_path):
    database_path = tmp_path / "draft_workspace.sqlite3"
    configure_storage(database_path)

    assert get_draft_budget() == 930

    set_draft_budget(875)
    configure_storage(database_path)

    assert get_draft_budget() == 875
    with pytest.raises(ValueError, match="non-negative integer"):
        set_draft_budget(-1)


def test_target_total_fp_is_optional_and_persists(tmp_path):
    database_path = tmp_path / "draft_workspace.sqlite3"
    configure_storage(database_path)

    assert get_target_total_fp() is None

    set_target_total_fp(2650.5)
    configure_storage(database_path)

    assert get_target_total_fp() == 2650.5
    with pytest.raises(ValueError, match="non-negative number"):
        set_target_total_fp(-1)


def test_adding_an_unpriced_player_to_my_team_is_rejected(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = int(get_players_for_grid().iloc[0]["id"])
    set_player_price(player_id, 12)

    with pytest.raises(PlayerPriceRequiredError, match="Set an auction price"):
        set_player_on_my_team(player_id, True)


def test_existing_workspace_schema_is_migrated_with_the_price_column(tmp_path):
    database_path = tmp_path / "draft_workspace.sqlite3"
    conn = sqlite3.connect(database_path)
    try:
        conn.execute(
            """
            CREATE TABLE players (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL CHECK(position IN ('F', 'D', 'G')),
                selected INTEGER NOT NULL DEFAULT 0,
                on_my_team INTEGER NOT NULL DEFAULT 0 CHECK(on_my_team IN (0, 1)),
                current_season INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    configure_storage(database_path)
    conn = sqlite3.connect(database_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(players)")}
    finally:
        conn.close()

    assert {"price", "auction_price"}.issubset(columns)


def test_existing_tag_schema_is_migrated_for_player_evaluation_tags(tmp_path):
    database_path = tmp_path / "draft_workspace.sqlite3"
    conn = sqlite3.connect(database_path)
    try:
        conn.execute(
            """
            CREATE TABLE player_tags (
                player_id INTEGER NOT NULL,
                tag TEXT NOT NULL CHECK(tag IN ('PP1', 'PP2', 'PK1', 'PK2', 'Line1', 'Line2', 'Starter', 'Backup', '1A', '1B', 'contract', 'rookie', 'bounceback')),
                PRIMARY KEY (player_id, tag)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    configure_storage(database_path)
    conn = sqlite3.connect(database_path)
    try:
        definition = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'player_tags'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert "'contract'" in definition
    assert "'rookie'" in definition
    assert "'bounceback'" in definition
    assert "'red flag'" in definition


def test_my_team_position_grid_history_queries_are_limited_to_roster_ids(tmp_path, monkeypatch):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    forwards = get_players_for_position_grid("F")
    player_id = int(forwards.iloc[0]["id"])
    set_player_auction_price(player_id, 1)
    set_player_on_my_team(player_id, True)

    original_get_position_stat_rows = storage._get_position_stat_rows
    query_player_ids = []

    def capture_history_query(*args, **kwargs):
        query_player_ids.append(kwargs["player_ids"])
        return original_get_position_stat_rows(*args, **kwargs)

    monkeypatch.setattr(storage, "_get_position_stat_rows", capture_history_query)

    my_team_forwards = get_players_for_position_grid("F", my_team_only=True)

    assert my_team_forwards["id"].tolist() == [player_id]
    assert query_player_ids == [[player_id], [player_id], [player_id]]


def test_position_grid_rejects_unknown_position(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    with pytest.raises(ValueError, match="Unsupported position"):
        get_players_for_position_grid("X")
