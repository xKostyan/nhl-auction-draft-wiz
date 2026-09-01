# Page: Goalies

- **Menu position:** 4
- **Route:** `/goalies`
- **Module:** `src/pages/goalies.py`
- **Tests:** `tests/pages/goalies/`
- **Status:** Implemented placeholder

## Purpose

Provide a dedicated live-auction table for goalies. It is intended to stay
open in its own browser tab during the draft.

## UI and behavior

- The page header contains only the page title and player search control.
- The table header and menu entry use the goalie purple `#cc33ff`.
- An AG Grid table with an unlabeled **highlight** circle, **#**, **Player
  name**, **Game Starts**, **Average Performance**, **p GS**, **p TFP `<upcoming year>`**,
  **p AFP `<upcoming year>`**, **Tags**, and **Notes** columns, in that order.
  `p TFP` is the projected Total
  Fantasy Points and `p AFP` is the projected Average Fantasy Points per game,
  both sourced from the detected upcoming draft season. Player database ids are
  retained internally for updates but are never displayed.
- **p GS** shows the player's projected game starts for the detected upcoming
  draft season.
- Columns auto-size from their cell contents; header text does not determine
  their default width. All column headers are centered, wrap to multiple lines,
  and grow the header row as needed; cell values do not wrap. Cell values,
  controls, and inline graphs are vertically centered. Cell text is 16px
  (2px larger than the default table value size).
- Rows are 60px high to accommodate current and future inline player graphs.
- **Average Performance** is a resizable 150px inline combination chart
  covering every imported goalie season. A blue line shows projected average
  fantasy points and bars show actual average fantasy points, with missing
  values shown as zero. Its fixed scale is 0-12; actual bars are red below
  7.0, orange through 7.5, yellow through 8.0, and green above 8.0.
- **Tags** is a resizable 160px compact display of selected tags, or a subtle
  `+` when no tags are set. Click the cell to open a temporary picker for
  `Starter`, `Backup`, `1A`, and `1B`, then click **Done** to close it. Tags
  are left-aligned. Always-visible selected tags use 11px text; the picker
  buttons use 9px text. `Starter` and `1A` use a green hue, `1B` uses a yellow
  hue, and `Backup` uses a red hue; selections persist in the workspace.
- **Notes** is the last, resizable 220px column. Click a cell to open a
  multi-line text editor; saved notes wrap within the cell and persist in the
  workspace. Visible note text is 14px.
- **Game Starts** is a 150px inline combination chart covering every goalie
  season in the imported workspace, including the upcoming season. A blue line
  shows projected game starts and bars show actual game starts; either missing
  value is displayed as zero. The chart's scale is fixed at 0-70. Actual bars
  are red below 30 starts, yellow from 30 through 42 starts, and green above
  42 starts. Every actual bar has a 9px value label centered vertically over
  the chart and above the chart marks; hovering a year shows both values. This
  column can be resized from its default width, and the chart expands to use
  its full available width. Gaps between annual actual-value bars are 50%
  smaller than the original chart spacing.
- The table fills the remaining browser viewport below the persistent app
  header and menu, while retaining its own vertical scrollbar.
- A searchable typeahead above the table suggests only goalies as you type.
  Selecting a suggestion (or confirming an exact full name) selects and
  centers that player in the table.
- The 20px **highlight** circle is light gray by default, light blue for an
  unselected player on **My Team**, and green for the selected player. It is
  updated by player search and can be clicked to select a player.
- **#** is a clickable availability switch. On means the player is available
  for the draft; off means the player is `drafted`. Its 26px column cannot be
  resized.
- Each checkbox edit is persisted from AG Grid's JSON status-change events,
  including every change in a batched update.
- Drafted players remain in the table, with gray text and a light gray row
  background.
- Right-click a **Player name** for a custom menu. **Clear Tags** and **Clear
  Notes** remove those persisted values. **Add to My Team** persistently adds
  the player to the My Team roster (and marks them drafted), while **Remove
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

- `src/pages/goalies.py` — route registration and Dash callback
- `src/pages/position_table.py` — shared position-grid layout and editing logic
- `src/storage.py` — persisted player status access
