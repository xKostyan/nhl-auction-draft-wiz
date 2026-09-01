# Page: My Team

- **Menu position:** 5
- **Route:** `/my-team`
- **Module:** `src/pages/my_team.py`
- **Tests:** `tests/pages/my_team/`
- **Status:** Implemented

## Purpose

Show the user's drafted roster, separated into **Forwards**, **Defencemen**,
**Utility**, **Goalies**, and **Bench** tables. A player is included only after
**Add to My Team** is selected from their player-name context menu. The
membership flag is stored in the workspace and survives restarts.

## UI and behavior

- A two-layer donut chart at the top shows the grand projected-TFP total in
  its center. Its inner ring is split among Forwards, Defencemen, Utility,
  and Goalies; its outer ring splits each group into its players. A white gap
  separates the rings. The groups use orange (F), green (D), blue (Utility),
  and purple (G), matching their table headers. Individual player slices use
  distinct shades within their group's color family.
- The page has fixed-size tables with 9 forward, 5 defencemen, 2 goalie, 2
  utility, and 4 bench slots. Every slot has an unlabeled numeric index;
  vacant slots are visibly styled and labeled **Empty slot**.
- Players are placed automatically: the main position tables fill first,
  forward/defenceman overflow fills Utility, and all remaining overflow
  (including goalies) fills Bench. Forwards, Defencemen, Utility, and Goalies
  are ordered by projected TFP from highest to lowest; Bench keeps spillover
  order.
- My Team rows are 50px high, with 12px spacing between tables. Tables retain the same player data, inline
  charts, Tags, and Notes as their matching position page. Utility has the
  skater columns plus **Position** after player name. Bench is intentionally
  limited to highlight, index, player name, **Position**, projected TFP, and
  projected AFP so skaters and goalies share it. The fixed-size tables suppress
  their unused internal vertical scrollbars.
- Goalies retain their position-specific tags (`Starter`, `Backup`, `1A`, and
  `1B`) when edited from the My Team Goalie table.
- The **Goalies** table includes **p GS** between Average Performance and
  projected TFP, showing projected starts for the detected draft season.
- Each heading has aligned columns and spacing for its table title, **p
  projection:** label, and projected-TFP total. Forwards, Defencemen, Utility,
  and Goalies show a total; Bench intentionally remains title-only. Missing
  player projections count as zero.
- The **Goalies** heading estimates projected TFP from 90% of each goalie's
  projected starts multiplied by projected AFP, capped at 140 combined starts.
  Active goalie slots are allocated first, then the highest-AFP Bench goalie,
  then remaining Bench goalies. It warns and shows the available 90%-share
  starts when the roster projects fewer than 140 starts.
- My Team tables intentionally omit the **#** availability column and do not
  gray rows: every displayed player is on the user's drafted team.
- Right-click a player name for **Clear Tags**, **Clear Notes**, or **Remove
  from My Team**. The menu is displayed above the tables and closes when you
  left-click outside it. **Add to My Team** is omitted because it is redundant
  here. Every table, heading, and chart refreshes from one snapshot after an
  edit, so automatic F/D/Utility/Bench placement remains consistent without
  an unused full position-page reload.
- When imported player data exists, the app's `/` route opens this page.
  An empty workspace still opens [Import data](./import-data.md).
- Each page render creates one roster snapshot, which is reused by all table
  rows, projected totals, goalie calculations, and chart slices. This prevents
  every displayed component from separately reloading and placing the same
  roster data. The snapshot's historical inline-chart data is queried only for
  the players on My Team, rather than every player at the relevant position.

## Related code

- `src/pages/my_team.py` — page registration and table callbacks
- `src/pages/position_table.py` — shared grids and context-menu action handler
- `src/storage.py` — durable My Team membership and player state

## TODO: Projection chart performance

- Use a lightweight chart query that avoids loading historical inline-chart
  data.
- Cache derived projection data and invalidate it after roster/import changes.
- Consider loading the chart after the roster tables render.
