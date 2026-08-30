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

- An AG Grid table with **Status**, **Player name**, **p TFP `<upcoming year>`**,
  and **p AFP `<upcoming year>`** columns, in that order. `p TFP` is the projected Total
  Fantasy Points and `p AFP` is the projected Average Fantasy Points per game,
  both sourced from the detected upcoming draft season. Player database ids are
  retained internally for updates but are never displayed.
- Columns auto-size from their cell contents; header text does not determine
  their default width.
- The table fills the remaining browser viewport below the persistent app
  header and menu, while retaining its own vertical scrollbar.
- **Status** is an editable checkbox. Checking it marks the player as
  `drafted`; clearing it marks the player as `available`.
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
