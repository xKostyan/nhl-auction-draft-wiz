import base64

import pytest

from src.data_loader import (
    load_players,
    load_stats,
    parse_uploaded_csv,
    parse_uploaded_keeper_prices,
    validate_players_df,
    validate_stats_df,
)


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


def test_load_stats_rejects_unsupported_position():
    with pytest.raises(ValueError):
        load_stats("X")


def test_parse_uploaded_csv_decodes_dash_upload_payload():
    csv_bytes = b"id,name,position\n1,Test Player,F\n"
    contents = "data:text/csv;base64," + base64.b64encode(csv_bytes).decode()

    df = parse_uploaded_csv(contents)

    assert list(df.columns) == ["id", "name", "position"]
    assert df.iloc[0]["name"] == "Test Player"


def test_parse_uploaded_keeper_prices_decodes_headerless_rows():
    csv_bytes = b'"Test Player, LW, ABC",$17\n"Goalie, G, XYZ",$0\n'
    contents = "data:text/csv;base64," + base64.b64encode(csv_bytes).decode()

    df = parse_uploaded_keeper_prices(contents)

    assert df.to_dict("records") == [
        {"name": "Test Player", "position": "F", "team": "ABC", "price": 17},
        {"name": "Goalie", "position": "G", "team": "XYZ", "price": 0},
    ]


def test_parse_uploaded_keeper_prices_supports_mac_roman_names():
    csv_bytes = b'"Tim St\x9ftzle, LW, Ott",$95\n'
    contents = "data:text/csv;base64," + base64.b64encode(csv_bytes).decode()

    df = parse_uploaded_keeper_prices(contents)

    assert df.iloc[0]["name"] == "Tim Stützle"


def test_parse_uploaded_keeper_prices_rejects_invalid_rows():
    csv_bytes = b'"Test Player, X, ABC",$17\n'
    contents = "data:text/csv;base64," + base64.b64encode(csv_bytes).decode()

    with pytest.raises(ValueError, match="unsupported position"):
        parse_uploaded_keeper_prices(contents)


def test_validate_players_df_raises_on_missing_columns():
    df = load_players().drop(columns=["position"])
    with pytest.raises(ValueError):
        validate_players_df(df)


def test_validate_stats_df_raises_on_missing_columns():
    df = load_stats("F").drop(columns=["stats_type"])
    with pytest.raises(ValueError):
        validate_stats_df(df, "forwards CSV")
