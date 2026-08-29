# AGENTS.md

## Mission

This repository is a Python dashboard project for NHL auction draft planning. The app uses:
- Python
- Dash for the web app
- AG Grid for interactive tables
- Plotly for charts
- pandas for CSV-driven analysis

The goal is to provide a single-agent-friendly environment for building and iterating on a draft planning dashboard without losing project context or conventions.

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

- Keep data loading, analysis, and UI code in separate modules.
- Treat CSV files in `csv-src-import-examples/` as source fixtures and keep the rest of the app data-driven.
- Do not write one giant app file for all logic.
- Keep callback logic thin and push heavy logic into pure Python helper functions.
- Preserve `projected` vs `actual` analytics as a first-class concept across filter logic, tables, and charts.
- Use pandas for merges and transformations; use Dash and Plotly only for presentation and interaction.

## Coding conventions

- Prefer Python 3.10+
- Use type hints where logic is non-trivial
- Use lowercase, descriptive names for DataFrame variables
- Keep CSV schema handling explicit and defensive
- Validate required columns before using them
- Keep UI selection state derived from data, not hidden globals

## Dashboard conventions

- AG Grid should be used for tabular exploration and ranking views
- Plotly should be used for charts and comparisons
- Dash callbacks should update data and charts from a common filtered DataFrame
- Avoid mixing business rules into layout code

## Persistent workspace model

This app is designed around a yearly import workflow:

- A yearly export from the upstream NHL stats app is imported into the local workspace once per season
- The imported dataset becomes the current draft workspace for that year
- Player status tracking is stored locally in SQLite and persists across app restarts
- Drafted, keeper, and unavailable players stay out of the active pool while still remaining in the workspace history
- The workspace can be reset with a clear action to allow the next season's dataset to be imported cleanly

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
