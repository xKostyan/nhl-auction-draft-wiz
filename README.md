# NHL Auction Draft Wiz

A Python + Dash + AG Grid + Plotly dashboard for evaluating NHL fantasy draft and auction decisions using CSV-based player and stat data.

**Current implementation stage:** the app only supports importing the yearly CSV export (via browser file upload) into a local persistent workspace, and clearing that workspace to prepare for the next season. There is no ranking, analysis, or chart/visualization functionality yet.

## Stack

- Python 3.10+
- Dash
- dash-ag-grid
- Plotly (planned for a later stage; not used yet)
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

The app expects 4 CSV files per yearly import:
- `players.csv` for player identity and roster metadata
- `f_stats.csv`, `d_stats.csv`, and `g_stats.csv` for position-specific stats

Each stats file carries a `stats_type` field for `projected` vs `actual` values, broken out per `year`. Since this app is used prior to a season starting, the current/upcoming season will only ever have `projected` data — its `actual` rows exist in the file but are always blank. The app detects the draft season automatically as the year whose `actual` rows are entirely empty.

**All years and both `projected`/`actual` data points found in the CSVs are imported and retained**, not just the upcoming draft season, so multi-year and projected-vs-actual historical comparisons remain possible once that analysis is built. Stats are stored per-player in a long format (one row per `year` / `stats_type` / stat name), which makes it easy to pull a single player's full history later.

## Persistent workspace and yearly import flow

The app stores imported data in a local SQLite database under `.workspace/draft_workspace.sqlite3`.

Typical usage:
1. On the dashboard, select the 4 CSV files (players, forwards, defencemen, goalies) using the upload controls — this works from any machine on the local network, not just localhost, so you can supply the files from whichever machine has them.
2. Click **Import season data**. The app stores every year/stats_type data point from the CSVs, and auto-detects the current draft season from the data (the year with only `projected`, no `actual`, data yet).
3. The workspace persists across app restarts.
4. Click **Clear workspace** when the next season's data is ready to import, then repeat step 1.

This gives the app a durable local-only import layer without requiring an external database. Player status tracking (drafted/keeper/unavailable) and draft/historical analysis are planned for a later stage.

## Development workflow rules

- Expand unit tests and smoke tests with each new feature or function
- Do not consider a feature complete until the relevant tests pass and any coverage gaps are fixed
- Commit and push completed work before treating it as finished
- Only work on branches named `feature*` or `bugfix*`; never on `main` or `master`

## Development notes

This repo is intentionally organized to be easy for a single AI coding agent to understand and extend without broad context loss.
