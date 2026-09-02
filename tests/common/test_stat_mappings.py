from src.stat_mappings import ESPN_TO_SQLITE_NAMES, SQLITE_COLUMN_DESCRIPTIONS


def test_espn_field_names_map_to_expected_storage_names():
    assert ESPN_TO_SQLITE_NAMES["+/-"] == "P_M"
    assert ESPN_TO_SQLITE_NAMES["TTOI ?"] == "TTOI"
    assert ESPN_TO_SQLITE_NAMES["16"] == "PTS"
    assert ESPN_TO_SQLITE_NAMES["SV%"] == "SVP"


def test_descriptions_resolve_known_mapped_storage_names():
    assert SQLITE_COLUMN_DESCRIPTIONS["PTS"] == "points"
    assert SQLITE_COLUMN_DESCRIPTIONS["SVP"] == "save percentage"
    assert SQLITE_COLUMN_DESCRIPTIONS[
        ESPN_TO_SQLITE_NAMES["TTOI ?"]
    ] == "time on ice"
    assert SQLITE_COLUMN_DESCRIPTIONS[
        ESPN_TO_SQLITE_NAMES["+/-"]
    ] == "plus/minus"


def test_undocumented_numeric_stat_codes_remain_explicitly_unknown():
    assert SQLITE_COLUMN_DESCRIPTIONS["19"] == "???"
    assert SQLITE_COLUMN_DESCRIPTIONS["_5"] == "???"
    assert SQLITE_COLUMN_DESCRIPTIONS["_99"] == "???"


def test_shots_against_has_a_description():
    assert SQLITE_COLUMN_DESCRIPTIONS["SA"] == "shots against"
