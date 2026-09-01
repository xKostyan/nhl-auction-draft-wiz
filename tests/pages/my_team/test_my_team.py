"""Tests for the My Team page."""

import dash_ag_grid as dag

from src.data_loader import load_players
from src.pages import my_team
from src.pages.position_table import get_position_rows, handle_player_cell_change
from src.storage import clear_workspace, configure_storage, import_yearly_dataset


def test_page_is_registered_at_the_expected_path_and_order():
    assert my_team.PATH == "/my-team"
    assert my_team.NAME == "My Team"
    assert my_team.ORDER == 4


def test_layout_has_one_undimmed_grid_per_position_without_drafted_column(tmp_path, walk_components):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()

    grids = [node for node in walk_components(my_team.layout()) if isinstance(node, dag.AgGrid)]

    assert [grid.id for grid in grids] == [
        "my-team-f-player-grid", "my-team-d-player-grid", "my-team-g-player-grid"
    ]
    assert all("drafted" not in [column["field"] for column in grid.columnDefs] for grid in grids)
    assert all("getRowStyle" not in grid.dashGridOptions for grid in grids)
    name_columns = [next(column for column in grid.columnDefs if column["field"] == "name") for grid in grids]
    assert all(column["cellRendererParams"] == {"allowAddToMyTeam": False} for column in name_columns)


def test_my_team_rows_are_the_persisted_team_subset_and_can_be_removed(tmp_path):
    configure_storage(tmp_path / "draft_workspace.sqlite3")
    clear_workspace()
    import_yearly_dataset()
    player_id = next(int(row.id) for row in load_players().itertuples(index=False) if row.position == "G")

    handle_player_cell_change(
        "G", [{"colId": "context_action", "value": "add-to-my-team:1", "data": {"id": player_id}}]
    )
    assert [row["id"] for row in get_position_rows("G", my_team_only=True)] == [player_id]

    handle_player_cell_change(
        "G",
        [{"colId": "context_action", "value": "remove-from-my-team:2", "data": {"id": player_id}}],
        my_team_only=True,
    )
    assert get_position_rows("G", my_team_only=True) == []
