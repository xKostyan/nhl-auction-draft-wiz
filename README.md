# NHL Auction Draft Wiz

A Python + Dash + AG Grid + Plotly dashboard for evaluating NHL fantasy draft and auction decisions using CSV-based player and stat data.

**Current implementation stage:** the app has a persistent top menu with six pages: **Import data**, dedicated **Forwards**, **Defencemen**, and **Goalies** live-auction tables, **My Team**, and **Player stats table**. Player stats table searches every imported player and renders that player's complete stored stat history. There is no ranking or analysis functionality yet. See [Pages documentation](docs/pages/) for details on each page.

## Stack

- Python 3.10+
- Dash
- dash-ag-grid
- Plotly (planned for a later stage; not used yet)
- pandas
- pytest

## Local environment setup

From the repo root, run the platform-specific setup script:

### Ubuntu / Linux

```bash
./setup.sh
```

### Windows

```bat
setup.bat
```

Each script creates the repo-local `.venv` when needed, upgrades `pip`, and
installs `requirements.txt`. To perform those steps manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Start the app

### Ubuntu / Linux

From the repo root:

```bash
./start-app.sh start
```

This opens a dedicated terminal window and launches the app using the repo-local `.venv`.

### Windows

From the repo root in Command Prompt or PowerShell:

```bat
start-app.bat start
```

This opens a dedicated terminal window and launches the app using the repo-local `.venv`.

The Dash app will print a URL such as:

```text
http://0.0.0.0:8050/
```

Open that URL in your browser to use the app.

## App structure and pages

The app has a persistent menu (top-left **☰ Menu** button) with 6 entries.
Each corresponds to one page module and one documentation page:

| # | Page name | Route | Module | Docs |
|---|-----------|-------|--------|------|
| 1 | Import data | `/import-data` | `src/pages/import_data.py` | [docs/pages/import-data.md](docs/pages/import-data.md) |
| 2 | Forwards | `/forwards` | `src/pages/forwards.py` | [docs/pages/forwards.md](docs/pages/forwards.md) |
| 3 | Defencemen | `/defencemen` | `src/pages/defencemen.py` | [docs/pages/defencemen.md](docs/pages/defencemen.md) |
| 4 | Goalies | `/goalies` | `src/pages/goalies.py` | [docs/pages/goalies.md](docs/pages/goalies.md) |
| 5 | My Team | `/my-team` | `src/pages/my_team.py` | [docs/pages/my-team.md](docs/pages/my-team.md) |
| 6 | Player stats table | `/player-stats-table` | `src/pages/player_stats_table.py` | [docs/pages/player-stats-table.md](docs/pages/player-stats-table.md) |

Landing page (`/`) behavior: if the workspace already has imported players,
it redirects to **My Team**; otherwise it redirects to **Import data**
so you're prompted to import a season first.

## Stop the app

### Ubuntu / Linux

```bash
./start-app.sh stop
```

### Windows

```bat
start-app.bat stop
```

If you started the app manually instead of using the helper script, press:

```text
Ctrl+C
```

in the terminal where it is running.

## Run tests

```bash
source .venv/bin/activate
python -m pytest
```

Tests are split into a `tests/common/` suite (data loading, storage, and
app-shell/menu/routing behavior) and one directory per page under
`tests/pages/<page>/`. Run a subset with:

```bash
python -m pytest tests/common               # shared/common tests only
python -m pytest tests/pages/import_data     # Import data page only
python -m pytest tests/pages/my_team         # My Team page only
```

## Project structure

- `app.py`: entry point for the Dash app
- `src/dashboard.py`: app shell (persistent menu + page routing + landing-page redirect)
- `src/components/`: shared UI building blocks (e.g. the persistent menu)
- `src/pages/`: one module per page, each registered via `dash.register_page` — see `docs/pages/`
- `src/data_loader.py`, `src/storage.py`: data loading/validation and persistent workspace storage
- `csv-src-import-examples/`: sample player and stat CSVs
- `tests/common/`: tests for shared/non-page-specific code
- `tests/pages/<page>/`: tests for one page each
- `docs/pages/`: one documentation file per page — see [docs/pages/](docs/pages/)
- `docs/sparklines.md`: reusable Dash AG Grid inline-chart implementation guide
- `AGENTS.md`: permanent agent instructions for Copilot and other AI tools
- `.github/copilot-instructions.md`: Copilot-specific guidance
- `.vscode/mcp.json`: Playwright MCP config for browser automation

## Data model

The app expects 4 CSV files per yearly import:
- `players.csv` for player identity and roster metadata
- `f_stats.csv`, `d_stats.csv`, and `g_stats.csv` for position-specific stats

Each stats file carries a `stats_type` field for `projected` vs `actual` values, broken out per `year`. Since this app is used prior to a season starting, the current/upcoming season will only ever have `projected` data — its `actual` rows exist in the file but are always blank. The app detects the draft season automatically as the year whose `actual` rows are entirely empty.

**All years and both `projected`/`actual` data points found in the CSVs are imported and retained**, not just the upcoming draft season, so multi-year and projected-vs-actual historical comparisons remain possible once that analysis is built. Stats are stored per-player in a long format (one row per `year` / `stats_type` / stat name), which makes it easy to pull a single player's full history later.

### Imported stat names

The scraper's compact, SQLite-safe stat names and their meanings are committed
in `src/stat_mappings.py`. Use `ESPN_TO_SQLITE_NAMES` to translate ESPN API
field names and `SQLITE_COLUMN_DESCRIPTIONS` to display their descriptive
meanings. A description of `"???"` marks an intentionally unresolved stat code;
do not infer its meaning.

## Persistent workspace and yearly import flow (Import data page)

The app stores imported data in a local SQLite database under `.workspace/draft_workspace.sqlite3`. Full details: [docs/pages/import-data.md](docs/pages/import-data.md).

Typical usage:
1. Open the **Import data** page from the menu (or land there automatically on an empty workspace) and select the 4 CSV files (players, forwards, defencemen, goalies) using the upload controls — this works from any machine on the local network, not just localhost, so you can supply the files from whichever machine has them.
2. Click **Import season data**. The app stores every year/stats_type data point from the CSVs, and auto-detects the current draft season from the data (the year with only `projected`, no `actual`, data yet).
3. The workspace persists across app restarts.
4. Click **Clear workspace** when the next season's data is ready to import, then repeat step 1.

This gives the app a durable local-only import layer without requiring an external database. The dedicated position pages provide drafted-status tracking. Other player
status types (keeper/unavailable) and draft/historical analysis are planned
for a later stage.

## Development workflow rules

- Expand unit tests and smoke tests with each new feature or function
- Do not consider a feature complete until the relevant tests pass and any coverage gaps are fixed
- When implementing or changing a page, update its documentation file under `docs/pages/` in the same change
- Commit and push completed work before treating it as finished
- Only work on branches named `feature*` or `bugfix*`; never on `main` or `master`

## Development notes

This repo is intentionally organized to be easy for a single AI coding agent to understand and extend without broad context loss.
