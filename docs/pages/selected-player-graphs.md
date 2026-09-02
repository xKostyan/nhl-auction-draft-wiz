# Page: Selected player graphs

- **Menu position:** 7
- **Route:** `/selected-player-graphs`
- **Module:** `src/pages/selected_player_graphs.py`
- **Tests:** `tests/pages/selected_player_graphs/`
- **Status:** Player selection implemented; graph content pending

## Purpose

Provide a dedicated browser-tab companion surface for the player currently
highlighted from any live-auction or My Team table.

## UI and behavior

- The page currently displays the selected player's name, or **No player
  highlighted.** until one is selected.
- Click the highlight circle or select **View selected player graphs** from a
  player-name context menu on the Forwards, Defencemen, Goalies, or My Team
  pages to replace the shared workspace selection.
- The page checks the shared SQLite workspace once per second, so a dedicated
  browser tab refreshes after a player is selected in another open tab.
- The selection is cleared when the workspace is cleared or a new dataset is
  imported, preventing an old player selection from appearing in the next
  season's workspace.

## Not yet implemented

- Position-specific graph cards and chart data.

## Related code

- `src/pages/selected_player_graphs.py` — route, display helper, and refresh
  callback
- `src/storage.py` — shared selected-player persistence
- `src/pages/position_table.py` — player-table selection action handling
