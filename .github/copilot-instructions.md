# Copilot Instructions for nhl-auction-draft-wiz

## Project overview

This repo is a Python dashboard project for NHL auction draft planning. The stack is:
- Python
- Dash
- AG Grid
- Plotly
- pandas

The app will analyze player and stat CSV data, compare projected vs actual performance, and present ranked draft options in an interactive dashboard.

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
   - merge player and stat tables

3. Draft analysis logic
   - `src/analysis.py`
   - compute rankings and value comparisons
   - separate business logic from UI code

4. Dash dashboard layer
   - `src/dashboard.py`
   - render AG Grid tables and Plotly charts
   - keep callbacks thin and use shared data transformations

5. App entry point
   - `app.py`
   - starts the Dash server on port 8050

## Conventions specific to this repo

- Keep `projected` and `actual` as first-class concepts in the data model and UI
- Use the `F`, `D`, and `G` position codes consistently
- Treat CSV files as the canonical fixture source for development
- Keep data choice and filtering logic in helper functions rather than inline in callbacks
- Use pandas for all data shaping and joins; use Dash/Plotly only for presentation
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

- Import the upstream CSV export once per season into `.workspace/draft_workspace.sqlite3`
- Track player state as `available`, `drafted`, `keeper`, or `unavailable`
- Keep the workspace durable across app restarts
- Clear the workspace before importing the next year's dataset

The SQLite implementation lives in `src/storage.py` and should be treated as the source of truth for player availability and draft state.

## Browser testing setup

This repo includes Playwright MCP support for Dash UI validation:

- config: `.vscode/mcp.json`
- use Playwright to validate page rendering and user flows after UI changes

## Related project docs

- `AGENTS.md`: permanent agent instructions
- `README.md`: quick-start and overview
- `.vscode/mcp.json`: MCP config
