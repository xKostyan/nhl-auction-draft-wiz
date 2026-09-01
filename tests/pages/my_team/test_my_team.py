"""Tests for the My Team page."""

import dash_ag_grid as dag
import src.pages.position_table as position_table
from dash import dcc

from src.data_loader import load_players
from src.pages import my_team
from src.pages.position_table import (
    MY_TEAM_SLOT_COUNTS,
    get_my_team_table_rows,
    get_my_team_projected_tfp_total,
    get_my_team_goalie_projection,
    get_my_team_table_title,
    get_position_grid_rows,
    get_position_rows,
    handle_player_context_action,
)
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert my_team.PATH == "/my-team"
    assert my_team.NAME == "My Team"
    assert my_team.ORDER == 4


def test_layout_has_fixed_numbered_roster_slots_without_drafted_column(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    grids = [node for node in walk_components(my_team.layout()) if isinstance(node, dag.AgGrid)]
    chart = next(node for node in walk_components(my_team.layout()) if isinstance(node, dcc.Graph))

    assert chart.id == my_team.CHART_ID
    assert len(chart.figure.data) == 2
    assert chart.figure.layout.annotations[0].text.startswith("Projected TFP")

    assert [grid.id for grid in grids] == [
        "my-team-f-player-grid",
        "my-team-d-player-grid",
        "my-team-utility-player-grid",
        "my-team-g-player-grid",
        "my-team-bench-player-grid",
    ]
    assert all("drafted" not in [column["field"] for column in grid.columnDefs] for grid in grids)
    assert [len(grid.rowData) for grid in grids] == [9, 5, 2, 2, 4]
    assert [grid.dashGridOptions["rowHeight"] for grid in grids] == [40, 40, 40, 40, 40]
    assert [grid.style["height"] for grid in grids] == ["410px", "250px", "130px", "130px", "210px"]
    assert all("is_empty_slot" in grid.dashGridOptions["getRowStyle"]["function"] for grid in grids)
    assert all(grid.columnDefs[1]["field"] == "slot_number" for grid in grids)
    assert all(grid.columnDefs[1]["headerName"] == "" for grid in grids)
    name_columns = [next(column for column in grid.columnDefs if column["field"] == "name") for grid in grids]
    assert all(column["cellRendererParams"] == {"allowAddToMyTeam": False} for column in name_columns)
    utility = grids[2]
    assert [column["field"] for column in utility.columnDefs][:4] == [
        "search_focus", "slot_number", "name", "position"
    ]
    bench = grids[-1]
    assert [column["field"] for column in bench.columnDefs] == [
        "search_focus", "slot_number", "name", "position", "projected_tfp", "projected_afp"
    ]
    goalie = grids[3]
    assert [column["field"] for column in goalie.columnDefs][4:8] == [
        "average_performance_history", "projected_gs", "projected_tfp", "projected_afp"
    ]


def test_my_team_rows_are_the_persisted_team_subset_and_can_be_removed(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")

    handle_player_context_action("G", {"rowId": player_id, "value": {"action": "add-to-my-team"}})
    assert [row["id"] for row in get_position_rows("G", my_team_only=True)] == [player_id]

    handle_player_context_action(
        "G",
        {"rowId": player_id, "value": {"action": "remove-from-my-team"}},
        my_team_only=True,
    )
    assert get_position_rows("G", my_team_only=True) == []


def test_skater_table_titles_include_current_projected_tfp_totals(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")

    handle_player_context_action(
        "F", {"rowId": player_id, "value": {"action": "add-to-my-team"}}
    )

    forward = next(row for row in get_position_rows("F", my_team_only=True) if row["id"] == player_id)
    assert get_my_team_projected_tfp_total("F") == forward["projected_tfp"]
    assert get_my_team_table_title("F") == f"Forwards - p TFP 2027: {forward['projected_tfp']:.2f}"
    assert get_my_team_table_title("G") == "Goalies - p TFP 2027: 0.00 (Warning: projected starts 0.0/140)"
    assert get_my_team_table_title("bench") == "Bench"


def test_projected_tfp_total_treats_missing_values_as_zero(monkeypatch):
    monkeypatch.setattr(
        position_table,
        "get_my_team_table_rows",
        lambda _table: [
            {"projected_tfp": 100.0},
            {"projected_tfp": float("nan")},
            {"projected_tfp": None},
            {"is_empty_slot": True, "projected_tfp": None},
        ],
    )

    assert get_my_team_projected_tfp_total("F") == 100.0


def test_goalie_projection_uses_active_then_bench_priority_and_start_cap(monkeypatch):
    monkeypatch.setattr(position_table, "get_workspace_value", lambda _key: "2027")
    monkeypatch.setattr(
        position_table,
        "get_my_team_table_rows",
        lambda table: {
            "G": [
                {"id": 1, "projected_afp": 4, "game_starts_history": [{"year": 2027, "projected": 80}]},
                {"id": 2, "projected_afp": 3, "game_starts_history": [{"year": 2027, "projected": 80}]},
            ],
            "bench": [
                {"id": 3, "position": "G", "projected_afp": 8, "game_starts_history": [{"year": 2027, "projected": 50}]},
            ],
        }[table],
    )

    projection = get_my_team_goalie_projection()

    assert projection == {"projected_points": 492.0, "available_starts": 144.0, "counted_starts": 140.0}


def test_goalie_title_warns_when_ninety_percent_starts_are_below_cap(monkeypatch):
    monkeypatch.setattr(position_table, "get_workspace_value", lambda _key: "2027")
    monkeypatch.setattr(
        position_table,
        "get_my_team_goalie_projection",
        lambda: {"projected_points": 400.0, "available_starts": 120.0, "counted_starts": 120.0},
    )

    assert get_my_team_table_title("G") == "Goalies - p TFP 2027: 400.00 (Warning: projected starts 120.0/140)"


def test_empty_roster_slots_are_numbered_and_visually_identifiable(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    rows = get_position_grid_rows("F", my_team_only=True, slot_count=MY_TEAM_SLOT_COUNTS["F"])

    assert [row["slot_number"] for row in rows] == list(range(1, 10))
    assert all(row["is_empty_slot"] is True for row in rows)
    assert all(row["name"] == "Empty slot" for row in rows)


def test_skater_overflow_is_automatically_placed_in_utility_then_bench(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_ids = [
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "F"
    ][:12]

    for player_id in player_ids:
        handle_player_context_action(
            "F", {"rowId": player_id, "value": {"action": "add-to-my-team"}}
        )

    expected_ids = [row["id"] for row in get_position_rows("F", my_team_only=True)]
    assert [row["id"] for row in get_my_team_table_rows("F")[:9]] == expected_ids[:9]
    assert [row["id"] for row in get_my_team_table_rows("utility")[:2]] == expected_ids[9:11]
    assert get_my_team_table_rows("bench")[0]["id"] == expected_ids[11]
    assert get_my_team_table_rows("utility")[0]["position"] == "F"
    assert get_my_team_table_rows("bench")[0]["position"] == "F"
