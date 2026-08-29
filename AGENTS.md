# AGENTS.md

## Mission

This repository is a Python dashboard project for NHL auction draft planning. The app uses:
- Python
- Dash for the web app
- AG Grid for interactive tables
- Plotly for charts (planned for a later stage — not yet used)
- pandas for CSV-driven data handling

The goal is to provide a single-agent-friendly environment for building and iterating on a draft planning dashboard without losing project context or conventions.

**Current implementation stage:** the app is a multi-page Dash app with a persistent top menu offering 2 pages: **1 - Import data** (`/import-data`, fully implemented) and **2 - Data table 1** (`/data-table-1`, placeholder for the future data-analysis feature). There is no ranking, valuation, analysis, or charting/visualization logic yet — do not add any of that until it is explicitly requested. **Whenever a page's functionality changes, update that page's file under `docs/pages/` in the same change** — see "Pages, menu, and documentation structure" below.

## Repo layout

- `README.md`: quick start and project overview
- `.github/copilot-instructions.md`: Copilot-specific repo guidance
- `AGENTS.md`: permanent project-level instructions for AI agents
- `csv-src-import-examples/`: source CSV fixtures for players and stats
- `src/`: application logic
  - `src/dashboard.py`: app shell — persistent menu, page routing, landing-page redirect
  - `src/components/`: shared UI building blocks (e.g. the persistent menu, `src/components/menu.py`)
  - `src/pages/`: one module per page, each calling `dash.register_page(...)` — see "Pages, menu, and documentation structure" below
  - `src/data_loader.py`, `src/storage.py`: CSV loading/validation and persistent SQLite workspace storage (shared by all pages)
- `docs/pages/`: one documentation file per page, mirroring `src/pages/`
- `tests/common/`: tests for shared/non-page-specific code (data loading, storage, app shell)
- `tests/pages/<page>/`: tests for one page each, mirroring `src/pages/`
- `.vscode/mcp.json`: MCP config for browser automation

## Pages, menu, and documentation structure

This app is a Dash multi-page app (`Dash(use_pages=True, ...)`). Each page is:

1. A module in `src/pages/<page_name>.py` that calls `dash.register_page(__name__, path=..., name=..., order=...)` and defines a `layout(**kwargs)` function (not a static layout) plus its own callbacks.
2. Listed in the persistent menu automatically (`src/components/menu.py` renders every entry in `dash.page_registry`, ordered by `order`) — you do not need to hand-edit the menu when adding a page.
3. Documented in a matching `docs/pages/<page-name>.md` file (kebab-case, matching the route).
4. Tested in a matching `tests/pages/<page_name>/` directory.

Current pages (this table is the source of truth for page names/order used in future feature requests — refer to pages by these names):

| # | Page name | Route | Module | Docs | Tests | Status |
|---|-----------|-------|--------|------|-------|--------|
| 1 | Import data | `/import-data` | `src/pages/import_data.py` | `docs/pages/import-data.md` | `tests/pages/import_data/` | Implemented |
| 2 | Data table 1 | `/data-table-1` | `src/pages/data_table_1.py` | `docs/pages/data-table-1.md` | `tests/pages/data_table_1/` | Placeholder |

**Mandatory rule: whenever you implement, change, or extend a page's functionality, update its `docs/pages/<page-name>.md` file and its `tests/pages/<page_name>/` tests in the same change.** Do not let the docs or page-specific tests drift out of sync with the code — this is as required as the general testing rules below.

When adding a brand-new page: create the `src/pages/<name>.py` module (register + layout + callbacks), a `docs/pages/<name>.md` file, and a `tests/pages/<name>/` directory, and add a row to the table above (and to `docs/pages/README.md` and the root `README.md` table).

### Landing page behavior

`src/dashboard.py`'s `_landing_page_path()` decides where `/` redirects: to **Data table 1** if the workspace already has imported players, otherwise to **Import data**. If you add pages or change this rule, update this function, its tests in `tests/common/test_dashboard_shell.py`, and this document.

### Dash Pages implementation notes

- Page modules call `dash.register_page(...)` as an import-time side effect. Dash requires a `Dash(use_pages=True, ...)` app to already exist before that call succeeds, so `src/dashboard.py`'s `build_dashboard()` creates the app first and only then imports the page modules.
- Because of this, any test that imports `src.pages.*` needs an app to already exist; `tests/conftest.py` builds one eagerly at conftest-import time so this works transparently in every test file.
- `Dash(...)` must be created with `suppress_callback_exceptions=True`. Without it, the frontend renderer validates every callback's Output/Input ids against whichever page's layout is currently rendered, and throws "ID not found in layout" console errors for every other page's component ids (e.g. `upload-players-filename` while viewing a different page, or during the initial `/` redirect before any page layout is mounted). This is expected/required for multi-page apps, not a bug to "fix" by removing the flag.

## Required stack

Use the repository-local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then run the app:

```bash
source .venv/bin/activate
python app.py
```

The app should start from the repo root and serve the Dash dashboard locally.

## Build, test, and debug commands

- Install dependencies:
  `python -m pip install -r requirements.txt`
- Run the app:
  `python app.py`
- Run all tests:
  `python -m pytest`
- Run tests for shared/common code only:
  `python -m pytest tests/common`
- Run tests for one page only:
  `python -m pytest tests/pages/import_data`
  `python -m pytest tests/pages/data_table_1`
- Run one test file:
  `python -m pytest tests/common/test_data_loader.py`
- Run one test by name:
  `python -m pytest tests/common/test_data_loader.py::test_load_players`

## Architecture guardrails

- Keep data loading, storage, and UI code in separate modules (`src/data_loader.py`, `src/storage.py`, `src/dashboard.py`, `src/pages/*`, `src/components/*`).
- Treat CSV files in `csv-src-import-examples/` as source fixtures and keep the rest of the app data-driven.
- Do not write one giant app file for all logic; page-specific logic belongs in its own `src/pages/<page>.py` module.
- Keep callback logic thin and push heavy logic into pure Python helper functions (see `handle_workspace_action` in `src/pages/import_data.py`).
- Preserve `projected` vs `actual` as a first-class concept in the data model; the upcoming draft season will only ever have `projected` data.
- Use pandas for merges and transformations; use Dash only for presentation and interaction at this stage (no Plotly/analysis modules yet — do not add `src/analysis.py` or `dcc.Graph` until requested).
- The persistent menu (`src/components/menu.py`) must stay page-agnostic — it derives its entries from `dash.page_registry`, so adding a page should never require editing the menu component itself.

## Coding conventions

- Prefer Python 3.10+
- Use type hints where logic is non-trivial
- Use lowercase, descriptive names for DataFrame variables
- Keep CSV schema handling explicit and defensive
- Validate required columns before using them
- Keep UI selection state derived from data, not hidden globals

## Dashboard conventions

- Current app scope: page 1 ("Import data") provides 4 CSV upload controls, an "Import season data" button, a "Clear workspace" button, a status message, and an AG Grid table confirming the imported players; page 2 ("Data table 1") is a placeholder with no functionality yet.
- Do not add Plotly charts, ranking/filter views, or player status-editing UI until explicitly requested — keep implementation focused on what's in the pages table above and in each page's `docs/pages/*.md` file.
- Dash callbacks should stay thin wrappers around testable helper functions; avoid embedding business logic directly in `@dash.callback`/`@app.callback` bodies.
- Avoid mixing business rules into layout code.
- Page `layout` must be a function (not a static value) so it reflects live workspace state on every navigation.

## Persistent workspace model

This is the data model behind page 1 ("Import data", `src/pages/import_data.py`). This app is designed around a yearly import workflow:

- A yearly export from the upstream NHL stats app (4 CSVs: players, forwards, defencemen, goalies) is imported into the local workspace once per season, via browser file-upload controls so the app can be used from any machine on the local network, not just localhost.
- Every year and every `projected`/`actual` data point present in the source stats CSVs is imported and retained — not just the upcoming draft season — so multi-year, projected-vs-actual historical analysis features can be built later without re-importing. Stats are stored in `player_stats` as a long/EAV table (`player_id, year, stats_type, position, stat_name, stat_value`) rather than one wide row per year, which makes it simple to query a single stat across years or types for any player.
- The draft season is auto-detected from the stats data (the year whose `actual` rows are entirely empty, i.e. the season that hasn't started yet); no manual year entry is required. This is stored as `players.current_season` / `workspace_meta.current_season` for reference, but does not limit what history is stored.
- Player status defaults to `available` for every imported player and is stored locally in SQLite, persisting across app restarts. Status-editing (marking drafted/keeper/unavailable) is a planned future feature and is intentionally not yet exposed in the UI.
- The workspace can be reset with a clear action to allow the next season's dataset to be imported cleanly.

Use `get_player_stat_history(player_id)` in `src/storage.py` to fetch a player's full long-format history (year, stats_type, stat_name, stat_value), and `get_available_stat_years()` to list years currently stored. These are the intended building blocks for future historical-analysis features — prefer extending them over re-deriving data access patterns.

The storage layer lives in `src/storage.py` and writes to `.workspace/draft_workspace.sqlite3` by default.

## Browser automation and MCP

This repo is prepared for browser-driven UI testing using Playwright MCP.

- MCP config: `.vscode/mcp.json`
- Use Playwright for UI smoke tests, DOM validation, and rendering checks for Dash pages
- Keep browser tests focused on critical user flows, not full end-to-end exploration of every UI path

## Guardrails for AI-assisted work

- Do not invent missing scripts or tooling that does not exist in the repo
- If a command is not valid yet, document the intended command rather than pretending it exists
- Keep changes small and directly aligned to the repo mission
- Update `README.md` and `.github/copilot-instructions.md` when major project conventions change
- When adding new modules, keep the repo layout easy for a single agent to infer without broad exploration
- Every new feature or function must be accompanied by ongoing expansion of unit tests and smoke tests as part of implementation
- A feature cannot be marked as implemented until all relevant tests pass and any failing or missing coverage is resolved, expanded, or adjusted
- Whenever a page's implementation changes, update its `docs/pages/<page>.md` file and its `tests/pages/<page>/` tests in the same change (see "Pages, menu, and documentation structure" above)
- Any completed feature must be committed and pushed before the work is considered complete
- Local work is prohibited on `main` or `master`; only branches matching `feature*` or `bugfix*` are allowed

## Non-goals

- Do not add unnecessary microservices or external databases for a project that is still a local dashboard app
- Do not replace the CSV-based model with a hidden state system unless a clear requirement demands it
