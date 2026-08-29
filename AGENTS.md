# AGENTS.md

## Mission

This repository is a Python dashboard project for NHL auction draft planning. The app uses:
- Python
- Dash for the web app
- AG Grid for interactive tables
- Plotly for charts (planned for a later stage — not yet used)
- pandas for CSV-driven data handling

The goal is to provide a single-agent-friendly environment for building and iterating on a draft planning dashboard without losing project context or conventions.

**Current implementation stage:** the app only supports (1) importing the 4 expected yearly CSV files (players, forwards, defencemen, goalies) via browser file upload, and (2) clearing the local workspace to reset for the next season's import. There is no ranking, valuation, analysis, or charting/visualization logic yet — do not add any of that until it is explicitly requested.

## Repo layout

- `README.md`: quick start and project overview
- `.github/copilot-instructions.md`: Copilot-specific repo guidance
- `AGENTS.md`: permanent project-level instructions for AI agents
- `csv-src-import-examples/`: source CSV fixtures for players and stats
- `src/`: application logic
- `tests/`: automated tests
- `.vscode/mcp.json`: MCP config for browser automation

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
- Run one test file:
  `python -m pytest tests/test_data_loader.py`
- Run one test by name:
  `python -m pytest tests/test_data_loader.py::test_load_players`

## Architecture guardrails

- Keep data loading, storage, and UI code in separate modules (`src/data_loader.py`, `src/storage.py`, `src/dashboard.py`).
- Treat CSV files in `csv-src-import-examples/` as source fixtures and keep the rest of the app data-driven.
- Do not write one giant app file for all logic.
- Keep callback logic thin and push heavy logic into pure Python helper functions (see `handle_workspace_action` in `src/dashboard.py`).
- Preserve `projected` vs `actual` as a first-class concept in the data model; the upcoming draft season will only ever have `projected` data.
- Use pandas for merges and transformations; use Dash only for presentation and interaction at this stage (no Plotly/analysis modules yet — do not add `src/analysis.py` or `dcc.Graph` until requested).

## Coding conventions

- Prefer Python 3.10+
- Use type hints where logic is non-trivial
- Use lowercase, descriptive names for DataFrame variables
- Keep CSV schema handling explicit and defensive
- Validate required columns before using them
- Keep UI selection state derived from data, not hidden globals

## Dashboard conventions

- Current dashboard scope is limited to: 4 CSV upload controls, an "Import season data" button, a "Clear workspace" button, a status message, and an AG Grid table confirming the imported players.
- Do not add Plotly charts, ranking/filter views, or player status-editing UI until explicitly requested — keep the current implementation focused on import/clear only.
- Dash callbacks should stay thin wrappers around testable helper functions; avoid embedding business logic directly in `@app.callback` bodies.
- Avoid mixing business rules into layout code.

## Persistent workspace model

This app is designed around a yearly import workflow:

- A yearly export from the upstream NHL stats app (4 CSVs: players, forwards, defencemen, goalies) is imported into the local workspace once per season, via browser file-upload controls so the app can be used from any machine on the local network, not just localhost.
- The draft season is auto-detected from the stats data (the year whose `actual` rows are entirely empty, i.e. the season that hasn't started yet); no manual year entry is required.
- The imported dataset becomes the current draft workspace for that year.
- Player status defaults to `available` for every imported player and is stored locally in SQLite, persisting across app restarts. Status-editing (marking drafted/keeper/unavailable) is a planned future feature and is intentionally not yet exposed in the UI.
- The workspace can be reset with a clear action to allow the next season's dataset to be imported cleanly.

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
- Any completed feature must be committed and pushed before the work is considered complete
- Local work is prohibited on `main` or `master`; only branches matching `feature*` or `bugfix*` are allowed

## Non-goals

- Do not add unnecessary microservices or external databases for a project that is still a local dashboard app
- Do not replace the CSV-based model with a hidden state system unless a clear requirement demands it
