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
  name**, **Health (actual GP)**,
  **p TFP `<upcoming year>`**, and **p AFP `<upcoming year>`** columns, in
  that order. `p TFP` is the projected Total Fantasy Points and `p AFP` is the
  projected Average Fantasy Points per game, both sourced from the detected
  upcoming draft season. Player database ids are retained internally for
  updates but are never displayed.
- Columns auto-size from their cell contents; header text does not determine
  their default width. All column headers are centered, wrap to multiple lines,
  and grow the header row as needed; cell values do not wrap.
- **Health (actual GP)** is an inline vertical-bar chart of up to the five
  most recent actual games-played seasons, ordered oldest to newest. Every bar
  shares a fixed 0-84 GP scale. Bars are red for 0-50 GP, orange for 51-60,
  yellow for 61-71, and green for 72-84; hovering a bar shows its season and
  actual GP. The column is 110px wide. Rows are 60px high to accommodate
  current and future inline player graphs.
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
