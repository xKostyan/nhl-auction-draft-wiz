# Page: Forwards

- **Menu position:** 2
- **Route:** `/forwards`
- **Module:** `src/pages/forwards.py`
- **Tests:** `tests/pages/forwards/`
- **Status:** Implemented placeholder

## Purpose

Provide a dedicated live-auction table for forwards. It is intended to stay
open in its own browser tab during the draft.

## UI and behavior

- The page header contains only the page title and player search control.
- An AG Grid table with an unlabeled **highlight** circle, **#**, **Player
  name**, **Health (actual GP)**, **Average Performance**,
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
- **Health (actual GP)** is an inline vertical-bar chart of up to the five
  most recent actual games-played seasons, ordered oldest to newest. Every bar
  shares a fixed 0-84 GP scale. Bars are red for 0-50 GP, orange for 51-60,
  yellow for 61-71, and green for 72-84; hovering a bar shows its season and
  actual GP. The column is 110px wide and is vertically centered in a 50px
  chart area, leaving 5px clearance above and below. Rows are 60px high to
  accommodate current and future inline player graphs.
- **Average Performance** is a resizable 150px inline combination chart
  covering every imported forward season. A blue line shows projected average
  fantasy points and bars show actual average fantasy points, with missing
  values shown as zero. Its fixed scale is 0-6; actual bars are red through
  3.1, orange through 3.5, yellow through 3.9, and green above 3.9.
- **Tags** is a resizable 160px compact display of selected tags, or a subtle
  `+` when no tags are set. Click the cell to open a temporary picker for
  `PP1`, `PP2`, `PK1`, `PK2`, `Line1`, and `Line2`, then click **Done** to
  close it. Tags are left-aligned. Always-visible selected tags use 11px text;
  the picker buttons use 9px text. `1` tags use a green hue and `2` tags use a
  yellow hue; selections persist in the workspace.
- **Notes** is the last, resizable 220px column. Click a cell to open a
  multi-line text editor; saved notes wrap within the cell and persist in the
  workspace.
- See [Sparkline implementation](../sparklines.md) for the reusable Dash AG
  Grid renderer pattern.
- The table fills the remaining browser viewport below the persistent app
  header and menu, while retaining its own vertical scrollbar.
- A searchable typeahead above the table suggests only forwards as you type.
  Selecting a suggestion (or confirming an exact full name) selects and
  centers that player in the table.
- The 20px **highlight** circle is light gray by default and green for the
  selected player. It is updated by player search and can be clicked to select
  a player.
- **#** is a clickable availability switch. On means the player is available
  for the draft; off means the player is `drafted`. Its 26px column cannot be
  resized.
- Each checkbox edit is persisted from AG Grid's JSON status-change events,
  including every change in a batched update.
- Drafted players remain in the table, with gray text and a light gray row
  background.
- Rows are loaded from and edits are persisted to the local SQLite workspace,
  so drafted state survives app restarts.

## Not yet implemented

- Additional position-specific stats columns, filters, rankings, and
  player-detail views.

## Related code

- `src/pages/forwards.py` — route registration and Dash callback
- `src/pages/position_table.py` — shared position-grid layout and editing logic
- `src/storage.py` — persisted player status access
