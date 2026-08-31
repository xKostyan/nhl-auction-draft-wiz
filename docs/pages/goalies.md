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
- An AG Grid table with an unlabeled **highlight** circle, **#**, **Player
  name**, **Game Starts**, **p TFP `<upcoming year>`**,
  and **p AFP `<upcoming year>`** columns, in that order. `p TFP` is the projected Total
  Fantasy Points and `p AFP` is the projected Average Fantasy Points per game,
  both sourced from the detected upcoming draft season. Player database ids are
  retained internally for updates but are never displayed.
- Columns auto-size from their cell contents; header text does not determine
  their default width. All column headers are centered, wrap to multiple lines,
  and grow the header row as needed; cell values do not wrap. Cell values,
  controls, and inline graphs are vertically centered. Cell text is 16px
  (2px larger than the default table value size).
- Rows are 60px high to accommodate current and future inline player graphs.
- **Game Starts** is a 150px inline combination chart covering every goalie
  season in the imported workspace, including the upcoming season. A blue line
  shows projected game starts and bars show actual game starts; either missing
  value is displayed as zero. The chart's scale is fixed at 0-70. Actual bars
  are red below 30 starts, yellow from 30 through 42 starts, and green above
  42 starts. Every actual bar shows its value in 9px text, inside taller bars
  or immediately above shorter bars; hovering a year shows both values. This
  column can be resized from its default width.
- The table fills the remaining browser viewport below the persistent app
  header and menu, while retaining its own vertical scrollbar.
- A searchable typeahead above the table suggests only goalies as you type.
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

- `src/pages/goalies.py` — route registration and Dash callback
- `src/pages/position_table.py` — shared position-grid layout and editing logic
- `src/storage.py` — persisted player status access
