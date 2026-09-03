# Page: Selected player graphs

- **Menu position:** 7
- **Route:** `/selected-player-graphs`
- **Module:** `src/pages/selected_player_graphs.py`
- **Tests:** `tests/pages/selected_player_graphs/`
- **Status:** Implemented

## Purpose

Provide a dedicated browser-tab companion surface for the player currently
highlighted from any live-auction or My Team table.

## UI and behavior

- The page displays the selected player's name, or **No player highlighted.**
  until one is selected.
- Click the highlight circle or select **Highlight the player** from a
  player-name context menu on the Forwards, Defencemen, Goalies, or My Team
  pages to replace the shared workspace selection.
- The page checks the shared SQLite workspace once per second, so a dedicated
  browser tab refreshes after a player is selected in another open tab.
- The selection is cleared when the workspace is cleared or a new dataset is
  imported, preventing an old player selection from appearing in the next
  season's workspace.
- The page refreshes the graph set alongside the selected player's name.
- Every player receives **AVG Performance**, which compares actual fantasy
  points average (bars) with projected values (line) by year.
- Skaters also receive actual-only **Health** (games played), **Hits**,
  **Blocks**, **Time on Ice** (total time on ice divided by games played and
  converted to minutes), and **Shots on Goal per Game** (total shots divided
  by games played), plus actual-versus-projected **Points** and **Special Teams
  Points** charts.
- Forwards additionally receive actual-versus-projected **Shooting
  Percentage** (goals divided by shots on goal), **Goals**, and **Assists**
  charts.
- Goalies additionally receive actual-versus-projected **Game Starts**, **Win
  Percentage**, and **Save Percentage** charts.

## Related code

- `src/pages/selected_player_graphs.py` — route, annual chart shaping, and
  refresh callbacks
- `src/storage.py` — shared selected-player persistence
- `src/pages/position_table.py` — player-table selection action handling
