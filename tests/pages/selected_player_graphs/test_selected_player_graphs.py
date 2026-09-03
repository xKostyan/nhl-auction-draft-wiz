"""Tests for the shared selected-player graphs surface."""

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
        "AVG Performance",
        "Health",
        "Points",
        "Special Teams Points",
        "Hits",
        "Blocks",
        "Time on Ice",
        "Shots on Goal per Game",
        "Shooting Percentage",
        "Goals",
        "Assists",
    ]
    points = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Points")
    health = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Health")
    assert [trace.name for trace in points.data] == ["Actual", "Projected"]
    assert [trace.name for trace in health.data] == ["Actual"]
    assert points.data[0].type == "bar"
    assert points.data[1].type == "scatter"


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


def test_defenceman_graphs_include_only_all_position_and_skater_metrics(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = next(row for row in get_players_for_grid().to_dict("records") if row["position"] == "D")
    set_selected_player(int(player["id"]))

    graphs = selected_player_graphs.build_player_graphs()

    assert [graph.figure.layout.title.text for graph in graphs] == [
        "AVG Performance",
        "Health",
        "Points",
        "Special Teams Points",
        "Hits",
        "Blocks",
        "Time on Ice",
        "Shots on Goal per Game",
    ]


def test_derived_skater_rates_use_the_imported_totals(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = next(row for row in get_players_for_grid().to_dict("records") if row["position"] == "F")
    set_selected_player(int(player["id"]))

    graphs = selected_player_graphs.build_player_graphs()
    time_on_ice = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Time on Ice")
    shots_per_game = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Shots on Goal per Game")
    shooting_percentage = next(graph.figure for graph in graphs if graph.figure.layout.title.text == "Shooting Percentage")

    assert time_on_ice.data[0].y[0] == 33339 / 61 / 60
    assert shots_per_game.data[0].y[0] == 66 / 61
    assert shooting_percentage.data[0].y[0] == 5 / 66 * 100
