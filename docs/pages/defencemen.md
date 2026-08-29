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

- An AG Grid table with only **Name** and **Status** columns. Player database
  ids are retained internally for updates but are never displayed.
- **Status** is an editable checkbox. Checking it marks the player as
  `drafted`; clearing it marks the player as `available`.
- Each checkbox edit is persisted from AG Grid's latest JSON status-change event.
- Drafted players remain in the table, with gray text and a light gray row
  background.
- Rows are loaded from and edits are persisted to the local SQLite workspace,
  so drafted state survives app restarts.

## Not yet implemented

- Position-specific stats columns, filters, rankings, and player-detail views.

## Related code

- `src/pages/defencemen.py` — route registration and Dash callback
- `src/pages/position_table.py` — shared position-grid layout and editing logic
- `src/storage.py` — persisted player status access
