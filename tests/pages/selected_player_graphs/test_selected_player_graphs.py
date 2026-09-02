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

    assert layout.className == "selected-player-graphs-page"
    assert interval.interval == 1_000
    assert player_name.children == "No player highlighted."


def test_refresh_shows_the_shared_selected_player_name(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player = get_players_for_grid().iloc[0]
    set_selected_player(int(player["id"]))

    assert selected_player_graphs.refresh_selected_player_name(1) == player["name"]
