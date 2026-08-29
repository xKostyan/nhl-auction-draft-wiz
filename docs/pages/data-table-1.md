# Page: Data table 1

- **Menu position:** 2
- **Route:** `/data-table-1`
- **Module:** `src/pages/data_table_1.py`
- **Tests:** `tests/pages/data_table_1/`
- **Status:** Placeholder (not yet implemented)

## Purpose

Reserved for the future data-analysis feature: historical projected-vs-actual
comparisons for each player across the seasons stored in the workspace (see
`src/storage.py`'s `get_player_stat_history()` / `get_available_stat_years()`
for the data access points this page is expected to build on).

## Current behavior

- Renders a static placeholder message. No data, tables, filters, or charts
  are implemented yet.
- This is also the app's landing page whenever the workspace already has
  imported players (see [Import data](./import-data.md) and
  `src/dashboard.py`'s `_landing_page_path()`), since that's the more useful
  default view once a season has been imported.

## Not yet implemented

- Everything: this page has no real functionality yet. When it is
  implemented, update this document (and add/expand
  `tests/pages/data_table_1/`) alongside the code change, per the rules in
  `AGENTS.md`.

## Related code

- `src/pages/data_table_1.py` — page registration and placeholder layout
