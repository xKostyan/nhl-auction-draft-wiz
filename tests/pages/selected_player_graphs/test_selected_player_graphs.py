"""Tests for the shared selected-player graphs surface."""

from pathlib import Path

from dash import dcc, html

from src.pages import selected_player_graphs
from src.storage import (
    clear_workspace,
    configure_storage,
    get_players_for_grid,
    import_yearly_dataset,
    set_selected_player,
)


def test_page_is_registered_at_the_expected_path_and_order():
    assert selected_player_graphs.PATH == "/selected-player-graphs"
    assert selected_player_graphs.NAME == "Selected player graphs"
    assert selected_player_graphs.ORDER == 6


def test_layout_shows_an_empty_message_and_refresh_interval(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()

    layout = selected_player_graphs.layout()
    interval = next(node for node in walk_components(layout) if isinstance(node, dcc.Interval))
    player_name = next(node for node in walk_components(layout) if getattr(node, "id", None) == selected_player_graphs.PLAYER_NAME_ID)
    graph_container = next(
        node for node in walk_components(layout) if getattr(node, "id", None) == selected_player_graphs.GRAPH_CONTAINER_ID
    )

    assert layout.className == "selected-player-graphs-page"
    assert interval.interval == 1_000
    assert player_name.children == "No player highlighted."
    assert graph_container.children == []


def test_refresh_shows_the_shared_selected_player_name(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = get_players_for_grid().iloc[0]
    set_selected_player(int(player["id"]))

    assert selected_player_graphs.refresh_selected_player_name(1) == player["name"]


def test_forward_graphs_include_all_skater_and_forward_metrics(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = next(row for row in get_players_for_grid().to_dict("records") if row["position"] == "F")
    set_selected_player(int(player["id"]))

    graphs = selected_player_graphs.refresh_selected_player_graphs(1)

    assert [graph.figure.layout.title.text for graph in graphs] == [
        "Health",
        "AVG Performance",
        "Time on Ice",
        "Assists per Game",
        "Points",
        "Special Teams Points",
        "Shots on Goal per Game",
        "Shooting Percentage",
        "Goals",
        "Hits per Game",
        "Blocks per Game",
    ]
    points = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Points")
    health = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Health")
    assert [trace.name for trace in points.data] == ["Actual", "Projected"]
    assert [trace.name for trace in health.data] == ["Actual"]
    assert points.data[0].type == "bar"
    assert points.data[1].type == "scatter"
    assert points.layout.showlegend is False
    assert points.layout.height == selected_player_graphs._CHART_HEIGHT
    assert next(graph for graph in graphs if graph.figure is points).style == {
        "height": "260px",
        "width": "100%",
    }
    assert health.data[0].marker.color[0] == "#f9a825"
    average_performance = next(
        graph.figure for graph in graphs if graph.figure.layout.title.text == "AVG Performance"
    )
    assert average_performance.data[0].marker.color[0] == "#d32f2f"
    time_on_ice = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Time on Ice")
    assert [trace.name for trace in time_on_ice.data] == ["Actual", "Projected"]
    assert time_on_ice.data[0].marker.color[0] == "#d32f2f"
    expected_yaxis_maxima = {
        "Health": 84,
        "AVG Performance": 6,
        "Time on Ice": 25,
        "Points": 120,
        "Special Teams Points": 60,
        "Hits per Game": 2,
        "Blocks per Game": 1.5,
        "Shots on Goal per Game": 6,
        "Shooting Percentage": 20,
        "Goals": 60,
        "Assists per Game": 2,
    }
    assert {
        graph.figure.layout.title.text: graph.figure.layout.yaxis.range[1] for graph in graphs
    } == expected_yaxis_maxima
    assert all(
        [trace.name for trace in graph.figure.data] == ["Actual", "Projected"]
        for graph in graphs
        if graph.figure.layout.title.text in {"Hits per Game", "Blocks per Game", "Shots on Goal per Game"}
    )


def test_goalie_graphs_are_limited_to_goalie_metrics(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = next(row for row in get_players_for_grid().to_dict("records") if row["position"] == "G")
    set_selected_player(int(player["id"]))

    graphs = selected_player_graphs.build_player_graphs()

    assert [graph.figure.layout.title.text for graph in graphs] == [
        "AVG Performance",
        "Game Starts",
        "Win Percentage",
        "Save Percentage",
    ]
    assert all([trace.name for trace in graph.figure.data] == ["Actual", "Projected"] for graph in graphs)
    assert {
        graph.figure.layout.title.text: graph.figure.layout.yaxis.range[1] for graph in graphs
    } == {
        "AVG Performance": 12,
        "Game Starts": 60,
        "Win Percentage": 0.8,
        "Save Percentage": 1,
    }
    save_percentage = next(
        graph.figure for graph in graphs if graph.figure.layout.title.text == "Save Percentage"
    )
    assert save_percentage.layout.yaxis.range[0] == 0.6
    assert {
        graph.figure.layout.title.text: graph.figure.data[0].marker.color[0] for graph in graphs
    } == {
        "AVG Performance": "#388e3c",
        "Game Starts": "#d32f2f",
        "Win Percentage": "#388e3c",
        "Save Percentage": "#388e3c",
    }


def test_defenceman_graphs_include_only_all_position_and_skater_metrics(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = next(row for row in get_players_for_grid().to_dict("records") if row["position"] == "D")
    set_selected_player(int(player["id"]))

    graphs = selected_player_graphs.build_player_graphs()

    assert [graph.figure.layout.title.text for graph in graphs] == [
        "Health",
        "AVG Performance",
        "Time on Ice",
        "Shots on Goal per Game",
        "Points",
        "Special Teams Points",
        "Hits per Game",
        "Blocks per Game",
    ]
    time_on_ice = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Time on Ice")
    assert time_on_ice.data[0].marker.color == "#1f77b4"
    assert next(
        graph.figure.layout.yaxis.range[1]
        for graph in graphs
        if graph.figure.layout.title.text == "Hits per Game"
    ) == 3
    assert next(
        graph.figure.layout.yaxis.range[1]
        for graph in graphs
        if graph.figure.layout.title.text == "Blocks per Game"
    ) == 3
    assert {
        graph.figure.layout.title.text: graph.figure.layout.yaxis.range[1] for graph in graphs
    } == {
        "Health": 84,
        "AVG Performance": 6,
        "Time on Ice": 27,
        "Points": 100,
        "Special Teams Points": 50,
        "Hits per Game": 3,
        "Blocks per Game": 3,
        "Shots on Goal per Game": 4,
    }


def test_derived_skater_rates_use_the_imported_totals(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = next(row for row in get_players_for_grid().to_dict("records") if row["position"] == "F")
    set_selected_player(int(player["id"]))

    graphs = selected_player_graphs.build_player_graphs()
    time_on_ice = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Time on Ice")
    hits_per_game = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Hits per Game")
    blocks_per_game = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Blocks per Game")
    shots_per_game = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Shots on Goal per Game")
    shooting_percentage = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Shooting Percentage")
    assists_per_game = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Assists per Game")

    assert time_on_ice.data[0].y[0] == 33339 / 61 / 60
    assert time_on_ice.data[1].y[-1] == 57530.01 / 79 / 60
    assert hits_per_game.data[0].y[0] == 101 / 61
    assert blocks_per_game.data[0].y[0] == 25 / 61
    assert shots_per_game.data[0].y[0] == 66 / 61
    assert shots_per_game.data[1].y[-1] == 99 / 79
    assert shooting_percentage.data[0].y[0] == 5 / 66 * 100
    assert assists_per_game.data[0].y[0] == 7 / 61
    assert assists_per_game.data[1].y[-1] == 14 / 79


def test_skater_bar_color_bands_match_the_player_tables():
    assert [selected_player_graphs._skater_health_color(value) for value in (50, 51, 61, 72)] == [
        "#d32f2f",
        "#ef6c00",
        "#f9a825",
        "#388e3c",
    ]
    assert [
        selected_player_graphs._skater_average_performance_color(value)
        for value in (3.1, 3.2, 3.6, 3.7, 4.1)
    ] == ["#d32f2f", "#ef6c00", "#f9a825", "#81c784", "#388e3c"]
    assert [selected_player_graphs._time_on_ice_color(value) for value in (14.9, 15, 16, 18)] == [
        "#d32f2f",
        "#ef6c00",
        "#f9a825",
        "#388e3c",
    ]


def test_goalie_bar_color_bands_match_the_requested_ranges():
    assert [selected_player_graphs._goalie_game_starts_color(value) for value in (29, 30, 43)] == [
        "#d32f2f",
        "#f9a825",
        "#388e3c",
    ]
    assert [
        selected_player_graphs._goalie_average_performance_color(value)
        for value in (6.9, 7, 7.6, 7.9, 8.3)
    ] == ["#d32f2f", "#ef6c00", "#f9a825", "#81c784", "#388e3c"]
    assert [selected_player_graphs._win_percentage_color(value) for value in (0.44, 0.45, 0.5, 0.55)] == [
        "#d32f2f",
        "#f9a825",
        "#81c784",
        "#388e3c",
    ]
    assert [selected_player_graphs._save_percentage_color(value) for value in (0.79, 0.8, 0.84, 0.88, 0.9)] == [
        "#d32f2f",
        "#ef6c00",
        "#f9a825",
        "#81c784",
        "#388e3c",
    ]


def test_graphs_use_a_compact_three_column_layout():
    stylesheet = (Path(__file__).parents[3] / "src" / "assets" / "app.css").read_text()

    assert ".selected-player-graphs {" in stylesheet
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in stylesheet
