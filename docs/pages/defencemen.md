# Page: Defencemen

- **Menu position:** 3
- **Route:** `/defencemen`
- **Module:** `src/pages/defencemen.py`
- **Tests:** `tests/pages/defencemen/`
- **Status:** Implemented placeholder

## Purpose

Provide a dedicated live-auction table for defencemen. It is intended to stay
open in its own browser tab during the draft.

## UI and behavior

- The page header contains only the page title and player search control.
- The table header and menu entry use the defencemen green `#5cd65c`.
- An AG Grid table with an unlabeled **highlight** circle, **#**, **Player
  name**, editable **k $$** (keeper price), editable **a $$** (auction price), **Health (actual GP)**, **Average Performance**,
  **p TFP `<upcoming year>`**, **p AFP `<upcoming year>`**, **Tags**, and
  **Notes** columns, in
  that order. `p TFP` is the projected Total Fantasy Points and `p AFP` is the
  projected Average Fantasy Points per game, both sourced from the detected
  upcoming draft season. Player database ids are retained internally for
  updates but are never displayed.
- Columns auto-size from their cell contents; header text does not determine
  their default width. All column headers are centered, wrap to multiple lines,
  and grow the header row as needed; cell values do not wrap. Cell values,
  controls, and inline graphs are vertically centered. Cell text is 16px
  (2px larger than the default table value size).
- **Health (actual GP)** is an inline combination chart of up to the five most
  recent actual games-played seasons, plus the upcoming projected season,
  ordered oldest to newest. A blue line shows projected GP with each point
  centered over its matching year's actual-GP bar, while every actual GP bar
  shares a fixed 0-84 scale and has its actual value centered over the chart.
  Bars are red for 0-50 GP, orange for 51-60, yellow for 61-71, and green for
  72-84; hovering a bar shows its season's projected and actual GP. The line is
  contained within the chart so its first and last points align with the first
  and last bar centers.
  The column defaults to 150px wide, can be resized, and expands to fill the
  available cell width. It is vertically centered in a 50px chart area,
  leaving 5px clearance above and below. Rows are 60px high to accommodate
  current and future inline player graphs.
- **Average Performance** is a resizable 150px inline combination chart
  covering every imported defenceman season. A blue line shows projected
  average fantasy points and bars show actual average fantasy points, with
  missing values shown as zero. Its fixed scale is 0-6; actual bars are red
  through 3.1, orange through 3.5, yellow below 3.7, light green from 3.7
  up to 4.1, and green from 4.1. The projected line starts at the center of
  the first bar and ends at the center of the last bar.
- **Tags** is a resizable 160px compact display of selected tags, or a subtle
  `+` when no tags are set. Click the cell to open a temporary picker for
  `PP1`, `PP2`, `PK1`, `PK2`, `Line1`, `Line2`, `contract`, `rookie`,
  `bounceback`, and `red flag`, then click **Done** to close it. `contract` marks a contract
  year, `rookie` marks future potential, and `bounceback` marks an unusually
  poor prior season with expected improvement. Tags are left-aligned.
  Always-visible selected tags use 11px text; the picker buttons use 9px text.
  `1` tags use a green hue, `2` tags use a yellow hue, `contract` uses light
  green, `rookie` uses gray, `bounceback` uses light blue, and `red flag` uses
  red; selections persist in the workspace.
- **Notes** is a resizable 220px column. Click a cell to open a
  multi-line text editor; saved notes wrap within the cell and persist in the
  workspace. Visible note text is 14px.
- **Watch** is the rightmost sortable 1-to-5 watch-rating column. Five circles
  show the current rating; click a circle to set and persist that rating.
- See [Sparkline implementation](../sparklines.md) for the reusable Dash AG
  Grid renderer pattern.
- The table fills the remaining browser viewport below the persistent app
  header and menu, while retaining its own vertical scrollbar.
- A searchable typeahead above the table suggests only defencemen as you type.
  Selecting a suggestion (or confirming an exact full name) highlights,
  centers, and persists that player for the **Selected player graphs**
  companion page.
- The 20px **highlight** circle is light gray by default, light blue for an
  unselected player on **My Team**, and green for the selected player. Clicking
  it selects the player in the shared workspace, which refreshes the
  [Selected player graphs](./selected-player-graphs.md) companion page.
- **#** is a clickable availability switch. On means the player is available
  for the draft; off means the player is `drafted`. Its 26px column cannot be
  resized.
- **k $$** is the editable non-negative whole-number keeper cost. **a $$** is the
  separate editable non-negative whole-number auction cost used for My Team budgets.
  Leave it blank when no value is known; entered values persist in the
  workspace across app restarts.
- Each checkbox edit is persisted from AG Grid's JSON status-change events,
  including every change in a batched update.
- Drafted players remain in the table, with gray text and a light gray row
  background.
- Right-click a **Player name** for a custom menu. **Highlight the player**
  selects and highlights the player for the shared companion page. **Clear Tags** and
  **Clear Notes** remove those persisted values. **Add to My Team** persistently
  adds the player to the My Team roster (and marks them drafted), while **Remove
  from My Team** only removes that roster membership. The menu is displayed
  above the grid and closes when you left-click outside it; the table reloads
  immediately after an action without affecting later Tags or Notes edits.
  The highlight circle changes to light blue immediately when membership is
  added, and back to gray when it is removed.
- **Add to My Team** is disabled with an explanatory tooltip when the player
  cannot fit within the fixed roster and Bench composition limits. A stale add
  attempt displays the same reason above the table.
- Rows are loaded from and edits are persisted to the local SQLite workspace,
  so drafted state survives app restarts.

## Not yet implemented

- Additional position-specific stats columns, filters, rankings, and
  player-detail views.

## Related code

- `src/pages/defencemen.py` — route registration and Dash callback
- `src/pages/position_table.py` — shared position-grid layout and editing logic
- `src/storage.py` — persisted player status access
