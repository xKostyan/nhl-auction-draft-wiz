from src.data_loader import load_players, load_stats


def test_load_players_has_core_columns():
    df = load_players()
    required = {"id", "name", "position"}
    assert required.issubset(set(df.columns))
    assert not df.empty


def test_load_stats_for_supported_positions():
    for position, expected in {"F": "f_stats.csv", "D": "d_stats.csv", "G": "g_stats.csv"}.items():
        df = load_stats(position)
        assert not df.empty
        assert "id" in df.columns
        assert "stats_type" in df.columns
