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

- A **Draft budget** panel persists a non-negative whole-number annual budget,
  defaulting to `$930`. It reports committed My Team price, remaining budget,
  the `$1` minimum reserved for every unfilled roster slot, flexible budget,
  and the maximum legal next bid after preserving the minimum for every other
  open slot. Only My Team players consume the budget; players drafted by other
  managers remain unavailable but do not affect it.
- An optional **Target total FP** text input (without increment/decrement
  controls) persists a projected-FP stretch goal. Remaining target FP is
  calculated from active Forwards, Defencemen, Utility, and the goalie
  90%-starts calculation (including bench goalies), then divided across empty
  active F, D, Utility, and Goalie slots. The aggregate status line is omitted
  to keep the budget panel compact.
- A player must have a Price before **Add to My Team** succeeds. Adding them
  then marks the player drafted and charges that price to the budget. Keepers
  and auction purchases follow this same workflow.
- The budget panel provides an advisory **Skaters / Goalies** allocation view.
  Its persisted percentage split drives planned budget, price spent, the
  required `$1` minimum, remaining allocation, and a per-slot guide. A 1%
  increment slider is the only split input: its left endpoint sets Skaters to
  100% and Goalies to 0%, its midpoint sets both to 50%, and its right endpoint
  reverses that split. Its floating value tooltip is hidden, leaving the drag
  handle as the only visible split control. Draft Budget panel text is one
  pixel smaller than the page default.
  Adjacent cells display the dollar amount allocated to Skaters and Goalies
  from the total budget. The slider uses no more than 75% of the
  allocation-controls row width. The budget panel is on the left of the
  projected-TFP chart; both use equal width on larger screens and stack on
  narrow screens.
- Empty active player slots show the remaining budget and average for their
  Skaters or Goalies allocation, followed by the target-FP average needed per
  empty active slot. Utility is included in the Skaters allocation. Empty Bench
  slots intentionally show neither budget nor target-FP guidance; bench skaters
  do not contribute to acquired projected FP, while bench goalie contribution
  remains part of the shared goalie calculation.
  Utility and Bench slots remain flexible and their required minimum is
  reflected in the global budget summary. These views do not prevent bids;
  **Max next bid** is the hard auction reference.
- A two-layer donut chart at the top-right shows the grand projected-TFP total in
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
- My Team rows are 50px high, with 12px spacing between tables. Tables retain
  the same player data, editable **$$** price, inline charts, Tags, and Notes as their matching
  position page. Health charts compare actual GP bars with a projected GP line;
  their 150px columns can be resized and their charts expand to fill the
  available cell width. Every inline projected line runs from the center of
  the first bar to the center of the last. Average Performance uses light
  green and green bands at 3.7 to below 4.1 and 4.1+ for skaters, and 7.9 to
  below 8.3 and 8.3+ for goalies. Utility has the
  skater columns plus **Position** after Price. Bench is intentionally
  limited to highlight, index, player name, **$$**, **Position**, projected TFP, and
  projected AFP so skaters and goalies share it. The fixed-size tables suppress
  their unused internal vertical scrollbars through both their AG Grid settings
  and My Team-scoped styling.
- Goalies retain their position-specific tags (`Starter`, `Backup`, `1A`, and
  `1B`) when edited from the My Team Goalie table.
- The **Goalies** table includes **p GS** between Average Performance and
  projected TFP, showing projected starts for the detected draft season.
- Each heading has aligned columns and spacing for its table title,
  **projection:** label, and projected-TFP total. Forwards, Defencemen, Utility,
  and Goalies show a total; Bench intentionally remains title-only. Missing
  player projections count as zero.
- The **Goalies** heading estimates projected TFP from 90% of each goalie's
  projected starts multiplied by projected AFP, capped at 140 combined starts.
  Active goalie slots are allocated first, then the highest-AFP Bench goalie,
  then remaining Bench goalies. It warns and shows the available 90%-share
  starts when the roster projects fewer than 140 starts.
- My Team tables intentionally omit the **#** availability column and do not
  gray rows: every displayed player is on the user's drafted team.
- Click a highlight circle or right-click a player name and choose **Highlight
  the player** to select and highlight the player for the shared
  [Selected player graphs](./selected-player-graphs.md) companion page.
  The context menu also provides **Clear Tags**, **Clear Notes**, or **Remove
  from My Team**. The menu is displayed above the tables and closes when you
  left-click outside it. **Add to My Team** is omitted because it is redundant
  here. Every table, heading, and chart refreshes from one snapshot after an
  edit, so automatic F/D/Utility/Bench placement remains consistent without
  an unused full position-page reload. Heading updates replace only their
  contents, preserving the page layout across repeated roster edits.
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
