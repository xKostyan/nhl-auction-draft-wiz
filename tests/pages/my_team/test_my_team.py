"""Tests for the My Team page."""

from pathlib import Path

import dash_ag_grid as dag
import pytest
import src.pages.position_table as position_table
from dash import dcc, html
from dash._utils import to_json

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
    handle_my_team_grid_update,
)
from src.storage import (
    clear_workspace,
    configure_storage,
    get_draft_budget,
    get_target_total_fp,
    get_workspace_value,
    get_selected_player,
    import_yearly_dataset,
    set_player_price,
    set_target_total_fp,
)


def add_to_my_team(position, player_id, price=1):
    """Add a priced player through the same context action used by the grid."""
    set_player_price(player_id, price)
    handle_player_context_action(
        position, {"rowId": player_id, "value": {"action": "add-to-my-team"}}
    )


def test_page_is_registered_at_the_expected_path_and_order():
    assert my_team.PATH == "/my-team"
    assert my_team.NAME == "My Team"
    assert my_team.ORDER == 4


def test_layout_has_fixed_numbered_roster_slots_without_drafted_column(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    page_layout = my_team.layout()
    grids = [node for node in walk_components(page_layout) if isinstance(node, dag.AgGrid)]
    chart = next(node for node in walk_components(page_layout) if isinstance(node, dcc.Graph))
    budget_input = next(
        node for node in walk_components(page_layout) if isinstance(node, dcc.Input)
        and node.id == my_team.BUDGET_INPUT_ID
    )
    target_input = next(
        node for node in walk_components(page_layout) if isinstance(node, dcc.Input)
        and node.id == my_team.TARGET_TOTAL_FP_INPUT_ID
    )

    assert budget_input.value == 930
    assert target_input.value is None
    assert target_input.type == "text"
    assert target_input.inputMode == "numeric"
    assert chart.id == my_team.CHART_ID
    assert len(chart.figure.data) == 2
    assert chart.figure.layout.annotations[0].text.startswith("Projected TFP")
    assert chart.figure.data[0].marker.colors == ("#ff8533", "#5cd65c", "#33adff", "#cc33ff")
    assert chart.figure.data[0].domain.x == (0.1, 0.9)
    assert chart.figure.data[1].hole == 0.84
    assert chart.figure.layout.height == 460
    overview = page_layout.children[1]
    assert overview.className == "my-team-overview"
    assert overview.children[0].className == "budget-panel"
    assert overview.children[1] is chart
    headings = [node for node in walk_components(page_layout) if isinstance(node, html.H3)]
    assert [heading.id for heading in headings] == [
        "my-team-f-title",
        "my-team-d-title",
        "my-team-utility-title",
        "my-team-g-title",
        "my-team-bench-title",
    ]
    assert all(heading.className == "my-team-table-heading" for heading in headings)
    assert all(len(heading.children) == 3 for heading in headings)
    assert headings[-1].children[1].children == ""
    assert headings[-1].children[2].children == ""

    assert [grid.id for grid in grids] == [
        "my-team-f-player-grid",
        "my-team-d-player-grid",
        "my-team-utility-player-grid",
        "my-team-g-player-grid",
        "my-team-bench-player-grid",
    ]
    assert all("drafted" not in [column["field"] for column in grid.columnDefs] for grid in grids)
    assert [len(grid.rowData) for grid in grids] == [9, 5, 2, 2, 4]
    assert [grid.dashGridOptions["rowHeight"] for grid in grids] == [50, 50, 50, 50, 50]
    assert all(grid.dashGridOptions["suppressVerticalScroll"] is True for grid in grids)
    assert [grid.style["height"] for grid in grids] == ["500px", "300px", "150px", "150px", "250px"]
    assert all("is_empty_slot" in grid.dashGridOptions["getRowStyle"]["function"] for grid in grids)
    assert all(grid.columnDefs[1]["field"] == "slot_number" for grid in grids)
    assert all(grid.columnDefs[1]["headerName"] == "" for grid in grids)
    name_columns = [next(column for column in grid.columnDefs if column["field"] == "name") for grid in grids]
    assert all(column["cellRendererParams"] == {"allowAddToMyTeam": False} for column in name_columns)
    utility = grids[2]
    assert [column["field"] for column in utility.columnDefs][:5] == [
        "search_focus", "slot_number", "name", "price", "position"
    ]
    utility_health = next(column for column in utility.columnDefs if column["field"] == "actual_gp_history")
    assert utility_health["width"] == 150
    assert utility_health["resizable"] is True
    assert utility_health["suppressAutoSize"] is True
    bench = grids[-1]
    assert [column["field"] for column in bench.columnDefs] == [
        "search_focus", "slot_number", "name", "price", "position", "projected_tfp", "projected_afp"
    ]
    goalie = grids[3]
    assert [column["field"] for column in goalie.columnDefs][5:9] == [
        "average_performance_history", "projected_gs", "projected_tfp", "projected_afp"
    ]


def test_layout_builds_one_my_team_snapshot(monkeypatch):
    calls = []

    def get_rows(position, **kwargs):
        calls.append((position, kwargs))
        return []

    monkeypatch.setattr(position_table, "get_position_rows", get_rows)
    monkeypatch.setattr(position_table, "get_workspace_value", lambda _key: "2027")
    monkeypatch.setattr(
        my_team,
        "get_workspace_value",
        lambda key: {
            "current_season": "2027",
            "budget_skater_percent": "80",
            "budget_goalie_percent": "20",
        }.get(key, ""),
    )

    my_team.layout()

    assert calls == [
        ("F", {"my_team_only": True}),
        ("D", {"my_team_only": True}),
        ("G", {"my_team_only": True}),
    ]


def test_layout_is_json_serializable_for_dash_page_rendering(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    assert to_json(my_team.layout())


def test_budget_metrics_are_direct_component_children(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    summary = my_team.build_budget_summary()
    metrics = summary.children[0]

    assert metrics.className == "budget-metrics"
    assert [metric.className for metric in metrics.children] == ["budget-metric"] * 4


def test_budget_allocation_table_uses_the_full_width_without_open_slots(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    summary = my_team.build_budget_summary()
    table = summary.children[3]

    assert [header.children for header in table.children[0].children.children] == [
        "Allocation", "Planned", "Spent", "Minimum", "Remaining", "Avg / slot"
    ]
    assert len(table.children[1].children[0].children) == 6


def test_budget_summary_reserves_one_dollar_for_each_empty_roster_slot(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    add_to_my_team("F", player_id, price=30)
    snapshot = position_table.build_my_team_snapshot()

    summary = my_team.get_budget_summary(snapshot=snapshot, budget=930)

    assert summary == {
        "total_budget": 930,
        "committed": 30,
        "empty_slots": 21,
        "reserved_minimums": 21,
        "available": 900,
        "flexible": 879,
        "max_next_bid": 880,
    }


def test_budget_summary_treats_a_legacy_blank_roster_price_as_zero(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    add_to_my_team("F", player_id, price=30)
    snapshot = position_table.build_my_team_snapshot()
    next(row for row in snapshot["F"] if row.get("id") == player_id)["price"] = float("nan")

    summary = my_team.get_budget_summary(snapshot=snapshot)

    assert summary["committed"] == 0


def test_budget_allocation_is_advisory_and_validates_percentages(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")
    add_to_my_team("G", player_id, price=40)
    snapshot = position_table.build_my_team_snapshot()

    rows = my_team.get_budget_allocation(
        {"skaters": 80, "goalies": 20}, snapshot=snapshot, budget=930
    )

    assert rows[0]["planned"] == 744
    assert rows[0]["open_slots"] == 16
    assert rows[1]["planned"] == 186
    assert rows[1]["committed"] == 40
    with pytest.raises(ValueError, match="total 100"):
        my_team.get_budget_allocation(
            {"skaters": 80, "goalies": 10}, snapshot=snapshot
        )


def test_budget_update_persists_budget_target_and_allocation_controls(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    _, status = my_team.build_budget_update(850, 2650, 80, 20)

    assert get_draft_budget() == 850
    assert get_target_total_fp() == 2650
    assert get_workspace_value("budget_skater_percent") == "80"
    assert get_workspace_value("budget_goalie_percent") == "20"
    assert status == ""


def test_target_fp_summary_uses_active_slots_and_bench_goalie_projection(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    snapshot = position_table.build_my_team_snapshot()

    summary = my_team.get_target_fp_summary(snapshot=snapshot, target_total_fp=2200)

    assert summary == {
        "target_total_fp": 2200,
        "acquired_fp": 0.0,
        "remaining_fp": 2200.0,
        "empty_active_slots": 18,
        "average_fp_per_active_slot": 2200 / 18,
    }


def test_empty_active_slots_show_budget_and_target_guidance_but_bench_does_not(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    set_target_total_fp(2200)
    snapshot = my_team._add_empty_slot_guidance(position_table.build_my_team_snapshot())

    assert snapshot["F"][0]["name"].startswith("Empty slot - $")
    assert snapshot["utility"][0]["name"].endswith("| 122.22 FP")
    assert snapshot["G"][0]["name"].endswith("| 122.22 FP")
    assert snapshot["bench"][0]["name"] == "Empty slot"


def test_my_team_rows_are_the_persisted_team_subset_and_can_be_removed(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")

    add_to_my_team("G", player_id)
    assert [row["id"] for row in get_position_rows("G", my_team_only=True)] == [player_id]
    assert get_position_rows("G", my_team_only=True)[0]["average_performance_history"]

    handle_player_context_action(
        "G",
        {"rowId": player_id, "value": {"action": "remove-from-my-team"}},
        my_team_only=True,
    )
    assert get_position_rows("G", my_team_only=True) == []


def test_goalie_tags_persist_from_the_my_team_goalie_table(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")
    add_to_my_team("G", player_id)

    handle_my_team_grid_update(
        "G",
        [{"colId": "tags", "value": ["Starter"], "data": {"id": player_id}}],
        None,
        "cellValueChanged",
    )

    goalie = next(row for row in get_position_rows("G", my_team_only=True) if row["id"] == player_id)
    assert goalie["tags"] == ["Starter"]


def test_price_changes_persist_from_the_my_team_table(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    add_to_my_team("F", player_id)

    handle_my_team_grid_update(
        "F",
        [{"colId": "price", "value": 28, "data": {"id": player_id}}],
        None,
        "cellValueChanged",
    )

    player = next(row for row in get_position_rows("F", my_team_only=True) if row["id"] == player_id)
    assert player["price"] == 28


def test_my_team_context_menu_selects_a_player_for_the_graphs_page(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")
    add_to_my_team("F", player_id)

    handle_my_team_grid_update(
        "F",
        None,
        {"rowId": player_id, "value": {"action": "select-player"}},
        "cellRendererData",
    )

    assert get_selected_player()["id"] == player_id


def test_context_menu_labels_the_shared_selection_action_as_highlight():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert 'menuAction("Highlight the player", "select-player")' in renderer


def test_my_team_health_renderer_displays_actual_games_played_values():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert "}, String(gamesPlayed))" in renderer
    assert 'bottom: "50%"' in renderer
    assert 'width: "100%"' in renderer


def test_my_team_average_performance_renderer_has_position_specific_green_bands():
    renderer = (
        Path(__file__).parents[3] / "src" / "assets" / "dashAgGridComponentFunctions.js"
    ).read_text()

    assert 'actual < 3.7 ? "#f9a825" : actual < 4.1 ? "#81c784" : "#388e3c"' in renderer
    assert 'actual < 7.9 ? "#f9a825" : actual < 8.3 ? "#81c784" : "#388e3c"' in renderer


def test_skater_table_titles_include_current_projected_tfp_totals(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "F")

    add_to_my_team("F", player_id)

    forward = next(row for row in get_position_rows("F", my_team_only=True) if row["id"] == player_id)
    assert get_my_team_projected_tfp_total("F") == forward["projected_tfp"]
    assert get_my_team_table_title("F") == f"Forwards projection: {forward['projected_tfp']:.2f}"
    assert get_my_team_table_title("G") == "Goalies projection: (Warning: projected starts 0.0/140) 0.00"
    assert get_my_team_table_title("bench") == "Bench"


def test_projected_tfp_total_treats_missing_values_as_zero(monkeypatch):
    monkeypatch.setattr(
        position_table,
        "get_my_team_table_rows",
        lambda _table, **_kwargs: [
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
        lambda table, **_kwargs: {
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
        lambda **_kwargs: {
            "projected_points": 400.0,
            "available_starts": 120.0,
            "counted_starts": 120.0,
        },
    )

    assert get_my_team_table_title("G") == "Goalies projection: (Warning: projected starts 120.0/140) 400.00"


def test_projection_chart_uses_distinct_player_shades_within_each_group():
    assert my_team._player_color("F", 0) == "#ff8533"
    assert my_team._player_color("F", 1) == "#ff9d5c"
    assert my_team._player_color("D", 0) == "#5cd65c"
    assert my_team._player_color("utility", 0) == "#33adff"
    assert my_team._player_color("G", 0) == "#cc33ff"


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
        add_to_my_team("F", player_id)

    expected_ids = [
        row["id"]
        for row in sorted(
            get_position_rows("F", my_team_only=True),
            key=lambda row: (
                -position_table._finite_number(row["projected_tfp"]),
                row["name"].casefold(),
            ),
        )
    ]
    assert [row["id"] for row in get_my_team_table_rows("F")[:9]] == expected_ids[:9]
    assert [row["id"] for row in get_my_team_table_rows("utility")[:2]] == expected_ids[9:11]
    assert get_my_team_table_rows("bench")[0]["id"] == expected_ids[11]
    assert get_my_team_table_rows("utility")[0]["position"] == "F"
    assert get_my_team_table_rows("bench")[0]["position"] == "F"


def test_active_my_team_tables_sort_players_by_projected_tfp(monkeypatch):
    monkeypatch.setattr(
        position_table,
        "get_position_rows",
        lambda position, **_kwargs: {
            "F": [
                {"id": 1, "name": "Low", "projected_tfp": 100},
                {"id": 2, "name": "High", "projected_tfp": 300},
            ],
            "D": [],
            "G": [],
        }[position],
    )

    assert [row["name"] for row in get_my_team_table_rows("F")[:2]] == ["High", "Low"]


def test_my_team_update_refreshes_all_tables_after_removal(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_ids = [
        int(row.id) for row in load_players().itertuples(index=False) if row.position == "F"
    ][:10]
    for player_id in player_ids:
        add_to_my_team("F", player_id)

    promoted_player_id = get_my_team_table_rows("utility")[0]["id"]
    removed_player_id = get_my_team_table_rows("F")[0]["id"]
    update = my_team.build_my_team_update(
        "F",
        None,
        {"rowId": removed_player_id, "value": {"action": "remove-from-my-team"}},
        "cellRendererData",
    )

    forward_rows, _, utility_rows, *_ = update
    assert any(row["id"] == promoted_player_id for row in forward_rows)
    assert all(row.get("id") != promoted_player_id for row in utility_rows)
    forward_heading_children = update[len(my_team.TABLES)]
    assert len(forward_heading_children) == 3
    assert all(isinstance(child, html.Span) for child in forward_heading_children)
