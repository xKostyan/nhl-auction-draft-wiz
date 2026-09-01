# Page: My Team

- **Menu position:** 5
- **Route:** `/my-team`
- **Module:** `src/pages/my_team.py`
- **Tests:** `tests/pages/my_team/`
- **Status:** Implemented

## Purpose

Show the user's drafted roster, separated into **Forwards**, **Defencemen**,
**Goalies**, **Utility**, and **Bench** tables. A player is included only after
**Add to My Team** is selected from their player-name context menu. The
membership flag is stored in the workspace and survives restarts.

## UI and behavior

- The page has fixed-size tables with 9 forward, 5 defencemen, 2 goalie, 2
  utility, and 4 bench slots. Every slot has an unlabeled numeric index;
  vacant slots are visibly styled and labeled **Empty slot**.
- Players are placed automatically: the main position tables fill first,
  forward/defenceman overflow fills Utility, and all remaining overflow
  (including goalies) fills Bench.
- My Team rows are 40px high. Tables retain the same player data, inline
  charts, Tags, and Notes as their matching position page. Utility has the
  skater columns; Bench is intentionally limited to highlight, index, player
  name, projected TFP, and projected AFP so skaters and goalies share it.
- My Team tables intentionally omit the **#** availability column and do not
  gray rows: every displayed player is on the user's drafted team.
- Right-click a player name for **Clear Tags**, **Clear Notes**, or **Remove
  from My Team**. The menu is displayed above the tables and closes when you
  left-click outside it. **Add to My Team** is omitted because it is redundant
  here. The affected table reloads immediately after a menu action without
  affecting later Tags or Notes edits.
- When imported player data exists, the app's `/` route opens this page.
  An empty workspace still opens [Import data](./import-data.md).

## Related code

- `src/pages/my_team.py` — page registration and table callbacks
- `src/pages/position_table.py` — shared grids and context-menu action handler
- `src/storage.py` — durable My Team membership and player state
