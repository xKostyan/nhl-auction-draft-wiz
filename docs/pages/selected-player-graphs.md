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
- Skater charts begin with **Health**, **AVG Performance**, and **Time on
  Ice**, in that order, filling the first three-column row.
- Skater **Health** bars use the player-table games-played bands: red through
  50, orange through 60, yellow through 71, then green. **AVG Performance**
  uses its player-table skater bands: red through 3.1, orange through 3.5,
  yellow below 3.7, light green below 4.1, then green.
- **Time on Ice** compares actual (bars) and projected (line) minutes per
  game. Its actual bars are red below 15 minutes, orange below 16, yellow
  below 18, and green at 18 or more.
- Skaters also receive actual-only **Hits**, **Blocks**, and **Shots on Goal
  per Game** (total shots divided by games played), plus
  actual-versus-projected **Points** and **Special Teams Points** charts.
- Goalies receive **AVG Performance**, which compares actual fantasy points
  average (bars) with projected values (line) by year.
- Forwards additionally receive actual-versus-projected **Shooting
  Percentage** (goals divided by shots on goal), **Goals**, and **Assists**
  charts.
- Goalies additionally receive actual-versus-projected **Game Starts**, **Win
  Percentage**, and **Save Percentage** charts.
- Charts use a compact 260px height and a three-column grid so portrait
  displays show three charts per row.
- Legends are hidden because bars consistently represent actual values and
  lines consistently represent projected values.

## Related code

- `src/pages/selected_player_graphs.py` — route, annual chart shaping, and
  refresh callbacks
- `src/storage.py` — shared selected-player persistence
- `src/pages/position_table.py` — player-table selection action handling
