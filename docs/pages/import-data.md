# Page: Import data

- **Menu position:** 1
- **Route:** `/import-data`
- **Module:** `src/pages/import_data.py`
- **Tests:** `tests/pages/import_data/`
- **Status:** Implemented

## Purpose

Import the yearly players / forwards / defencemen / goalies CSV export into the
local persistent workspace, or clear the workspace to prepare for the next
season's import.

## UI

- Four `dcc.Upload` file-selection controls, one per required CSV:
  players, forwards, defencemen, goalies. Files are selected from the
  browser, so this works from any machine on the local network (not just
  localhost).
- **Import season data** button: reads all four selected CSVs, validates
  their required columns, and imports them into the workspace.
- **Clear workspace** button: deletes all imported players, stats, and
  status data so a new season can be imported.
- A status message showing the current workspace state or the result of the
  last action.
- A read-only AG Grid table listing every imported player with id, name,
  position, status, and current season.

## Data behavior

- All 4 files are required before an import can run; the UI reports which
  ones are missing otherwise.
- Every year and every `projected`/`actual` data point found in the stats
  CSVs is imported and retained (not just the upcoming draft season) — see
  `src/storage.py` for the historical storage model.
- The upcoming draft season is auto-detected as the year whose `actual` rows
  are entirely empty; this is stored as `current_season` for display only
  and does not limit what history is imported.
- Every imported player defaults to `available` status.

## Not yet implemented

  - Any ranking, filtering, or analysis of the imported data — see the
  [Data table 1](./data-table-1.md) page for that future work.

  Player drafted status is edited from the dedicated [Forwards](./forwards.md),
  [Defencemen](./defencemen.md), and [Goalies](./goalies.md) pages.

## Related code

- `src/pages/import_data.py` — page layout and callbacks
- `src/data_loader.py` — CSV parsing/validation, including browser-upload decoding
- `src/storage.py` — SQLite persistence, import/clear logic, historical data model
