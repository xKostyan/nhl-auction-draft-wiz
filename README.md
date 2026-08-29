# NHL Auction Draft Wiz

A Python + Dash + AG Grid + Plotly dashboard for evaluating NHL fantasy draft and auction decisions using CSV-based player and stat data.

## Stack

- Python 3.10+
- Dash
- dash-ag-grid
- Plotly
- pandas
- pytest

## Local environment setup

From the repo root:

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

## Project structure

- `app.py`: entry point for the Dash app
- `src/`: business logic and dashboard code
- `csv-src-import-examples/`: sample player and stat CSVs
- `tests/`: Python test suite
- `AGENTS.md`: permanent agent instructions for Copilot and other AI tools
- `.github/copilot-instructions.md`: Copilot-specific guidance
- `.vscode/mcp.json`: Playwright MCP config for browser automation

## Data model

The app expects CSV fixtures with:
- `players.csv` for player identity and roster metadata
- `f_stats.csv`, `d_stats.csv`, and `g_stats.csv` for position-specific stats
- a distinct `stats_type` field for `projected` vs `actual` values

## Persistent workspace and yearly import flow

The dashboard stores imports and player state in a local SQLite database under `.workspace/draft_workspace.sqlite3`.

Typical usage:
1. Import the yearly CSV export once at the start of the season
2. Mark players as `drafted`, `keeper`, or `unavailable` as the draft progresses
3. Keep the current workspace persistent across app restarts
4. Clear the workspace when the next season's data is ready to import

This gives the app a durable draft-management layer without requiring an external database.

## Development workflow rules

- Expand unit tests and smoke tests with each new feature or function
- Do not consider a feature complete until the relevant tests pass and any coverage gaps are fixed
- Commit and push completed work before treating it as finished
- Only work on branches named `feature*` or `bugfix*`; never on `main` or `master`

## Development notes

This repo is intentionally organized to be easy for a single AI coding agent to understand and extend without broad context loss.
