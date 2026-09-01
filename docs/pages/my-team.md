# Page: My Team

- **Menu position:** 5
- **Route:** `/my-team`
- **Module:** `src/pages/my_team.py`
- **Tests:** `tests/pages/my_team/`
- **Status:** Implemented

## Purpose

Show the user's drafted roster, separated into **Forwards**, **Defencemen**,
and **Goalies** tables. A player is included only after **Add to My Team** is
selected from their player-name context menu. The membership flag is stored in
the workspace and survives restarts.

## UI and behavior

- The page has one table per position, with the same player data, inline
  charts, Tags, and Notes as the matching position page.
- My Team tables intentionally omit the **#** availability column and do not
  gray rows: every displayed player is on the user's drafted team.
- Right-click a player name for **Clear Tags**, **Clear Notes**, or **Remove
  from My Team**. The menu is displayed above the tables and closes when you
  left-click outside it. **Add to My Team** is omitted because it is redundant
  here. The affected table reloads immediately after a menu action.
- When imported player data exists, the app's `/` route opens this page.
  An empty workspace still opens [Import data](./import-data.md).

## Related code

- `src/pages/my_team.py` — page registration and table callbacks
- `src/pages/position_table.py` — shared grids and context-menu action handler
- `src/storage.py` — durable My Team membership and player state
