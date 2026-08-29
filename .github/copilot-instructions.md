# Copilot Instructions for nhl-auction-draft-wiz

## Project overview

This repo is a Python dashboard project for NHL auction draft planning. The stack is:
- Python
- Dash
- AG Grid
- Plotly
- pandas

The app will eventually analyze player and stat CSV data, compare projected vs actual performance, and present ranked draft options in an interactive dashboard. **Current implementation stage:** the app only supports importing the yearly CSV export into the local workspace and clearing the workspace — no ranking/analysis logic or Plotly charts exist yet. Do not add analysis, ranking, or visualization features until explicitly requested.

## Required project setup

Use the repo-local virtual environment for all Python work:

```bash
cd /home/builder/Documents/nhl-auction-draft-wiz
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This repo is intended to be developed with a single AI coding agent. The environment and dependency state are stored in the repo under `.venv/` and `requirements.txt`.

## Build, test, and run commands

- Install dependencies:
  `python -m pip install -r requirements.txt`
- Run the app:
  `python app.py`
- Run the full test suite:
  `python -m pytest`
- Run one test file:
  `python -m pytest tests/test_data_loader.py`
- Run one test by name:
  `python -m pytest tests/test_data_loader.py::test_load_players`

## High-level architecture

The project is intentionally organized around a simple, AI-agent-friendly data flow:

1. CSV input layer
   - `csv-src-import-examples/players.csv`
   - `csv-src-import-examples/f_stats.csv`
   - `csv-src-import-examples/d_stats.csv`
   - `csv-src-import-examples/g_stats.csv`

2. Data loading and validation
   - `src/data_loader.py`
   - validate required columns
   - normalize positions and missing data
   - decode browser-uploaded CSV payloads (`parse_uploaded_csv`) as well as bundled sample fixtures

3. Persistent workspace / import layer
   - `src/storage.py`
   - imports the 4 expected CSVs (players, forwards, defencemen, goalies) into SQLite
   - auto-detects the draft season (the year with no `actual` results yet)
   - clears the workspace to prepare for the next season's import
   - **Not implemented yet:** ranking/valuation logic (`src/analysis.py` does not exist yet — do not add it until analysis is explicitly requested)

4. Dash dashboard layer
   - `src/dashboard.py`
   - exposes only: 4 CSV upload controls, an "Import season data" button, a "Clear workspace" button, a status message, and an AG Grid table confirming the imported players
   - **no Plotly charts or graphs are rendered at this stage** — do not add `dcc.Graph`/analysis views until requested
   - keep callback logic thin; the import/clear branching lives in the testable `handle_workspace_action` helper

5. App entry point
   - `app.py`
   - starts the Dash server on port 8050

## Conventions specific to this repo

- Keep `projected` and `actual` as first-class concepts in the data model (no `actual` data will exist for the upcoming draft season)
- Use the `F`, `D`, and `G` position codes consistently
- Treat CSV files as the canonical fixture source for development
- Keep data choice and filtering logic in helper functions rather than inline in callbacks
- Use pandas for all data shaping and joins; use Dash only for presentation at this stage (no Plotly yet)
- Preserve explicit column names and file names to reduce breakage in future agent-driven work

## AI-agent guardrails

- Read `AGENTS.md` first for repo-wide rules and structure
- Keep documentation current when architecture changes
- Do not invent missing build/test scripts or dependencies
- Prefer small, direct changes that match the repo’s data-first design
- Do not create hidden, untracked state for app logic; keep the app deterministic and testable
- Every new feature or function must include test and smoke-test expansion as part of the implementation
- A feature cannot be marked as implemented until all relevant tests pass and any gaps are resolved or expanded
- Completed work must be committed and pushed before it is considered done
- Work must happen only on `feature*` or `bugfix*` branches; `main` and `master` are not allowed

## Persistent workspace and import rules

This repo supports a yearly import workflow with a local persistent workspace database:

- Import is done via 4 browser file-upload controls (players, forwards, defencemen, goalies CSVs) so the app can be used from any machine on the local network, not just localhost
- Every year and every `projected`/`actual` data point present in the source stats CSVs is imported and retained (not just the upcoming draft season), to support future multi-year historical analysis
- Stats are stored long/EAV-style in `player_stats` (`player_id, year, stats_type, position, stat_name, stat_value`), so a single stat can be queried across years/types per player without reshaping wide rows
- The draft season is auto-detected from the stats data (the year whose `actual` rows are entirely empty); no manual year entry is required. It is tracked as `players.current_season` / `workspace_meta.current_season`, but does not restrict what history is stored
- Import the upstream CSV export once per season into `.workspace/draft_workspace.sqlite3`
- Track player state as `available`, `drafted`, `keeper`, or `unavailable` (status defaults to `available` on import; editing status is a future feature, not yet exposed in the UI)
- Keep the workspace durable across app restarts
- Clear the workspace before importing the next year's dataset
- Use `get_player_stat_history(player_id)` and `get_available_stat_years()` in `src/storage.py` as the entry points for reading historical data; extend these rather than adding parallel data-access helpers

The SQLite implementation lives in `src/storage.py` and should be treated as the source of truth for player availability and draft state.

## Browser testing setup

This repo includes Playwright MCP support for Dash UI validation:

- config: `.vscode/mcp.json`
- use Playwright to validate page rendering and user flows after UI changes

## Related project docs

- `AGENTS.md`: permanent agent instructions
- `README.md`: quick-start and overview
- `.vscode/mcp.json`: MCP config
