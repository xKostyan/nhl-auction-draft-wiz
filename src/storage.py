from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from .data_loader import (
    load_players,
    load_stats,
    validate_players_df,
    validate_stats_df,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / ".workspace" / "draft_workspace.sqlite3"

_DB_PATH = DEFAULT_DB_PATH


def configure_storage(path: str | Path | None = None) -> Path:
    """Set the SQLite database path for local workspace state."""
    global _DB_PATH
    _DB_PATH = Path(path) if path is not None else DEFAULT_DB_PATH
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    ensure_schema()
    return _DB_PATH


def db_connection() -> sqlite3.Connection:
    """Create a connection to the local SQLite workspace database."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema() -> None:
    """Create the schema for persistent player/workspace state."""
    conn = db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL CHECK(position IN ('F', 'D', 'G')),
                selected INTEGER NOT NULL DEFAULT 0,
                imported_year INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_status (
                player_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL CHECK(status IN ('available', 'drafted', 'keeper', 'unavailable')),
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                stats_type TEXT NOT NULL CHECK(stats_type IN ('projected', 'actual')),
                position TEXT NOT NULL CHECK(position IN ('F', 'D', 'G')),
                data_json TEXT NOT NULL,
                PRIMARY KEY (player_id, year, stats_type, position),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO workspace_meta (key, value) VALUES
                ('workspace_name', 'default'),
                ('current_year', '0'),
                ('last_imported_at', '')
            """
        )
        conn.commit()
    finally:
        conn.close()


def set_workspace_value(key: str, value: str) -> None:
    conn = db_connection()
    try:
        conn.execute(
            "INSERT INTO workspace_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def get_workspace_value(key: str) -> str:
    conn = db_connection()
    try:
        row = conn.execute("SELECT value FROM workspace_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else ""
    finally:
        conn.close()


def clear_workspace() -> None:
    """Delete all imported player/workspace state so a new season can be imported."""
    conn = db_connection()
    try:
        conn.execute("DELETE FROM player_stats")
        conn.execute("DELETE FROM player_status")
        conn.execute("DELETE FROM players")
        conn.execute("DELETE FROM workspace_meta")
        conn.executemany(
            "INSERT INTO workspace_meta (key, value) VALUES (?, ?)",
            [
                ("workspace_name", "default"),
                ("current_year", "0"),
                ("last_imported_at", ""),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def detect_draft_year(*stat_frames: pd.DataFrame) -> int:
    """Pick the upcoming draft season: the latest year with no 'actual' results yet.

    The yearly export always contains a fixed 'projected' and 'actual' row per
    player/year, but for a season that has not started, the 'actual' row exists
    structurally with every stat column left blank. Falls back to the max year
    present if every year already has some actual results (e.g. sample/test data).
    """
    all_years: set[int] = set()
    upcoming_years: set[int] = set()

    for frame in stat_frames:
        if frame is None or frame.empty or "year" not in frame.columns:
            continue
        stat_columns = [c for c in frame.columns if c not in ("id", "year", "stats_type")]
        for year, group in frame.groupby("year"):
            all_years.add(int(year))
            actual_rows = group[group["stats_type"] == "actual"]
            if not actual_rows.empty and actual_rows[stat_columns].isna().all(axis=None):
                upcoming_years.add(int(year))

    if upcoming_years:
        return max(upcoming_years)
    if all_years:
        return max(all_years)
    raise ValueError("Unable to detect a draft year: no year data found in the imported stat files.")


def import_yearly_dataset(
    players_df: pd.DataFrame | None = None,
    forward_df: pd.DataFrame | None = None,
    defense_df: pd.DataFrame | None = None,
    goalie_df: pd.DataFrame | None = None,
) -> dict[str, int]:
    """Import the four expected CSV datasets into the local SQLite workspace.

    This replaces any existing dataset. The draft season is detected automatically
    from the stats files (the season with only projected, no actual, data yet).
    When a dataset is omitted, the bundled sample CSV fixture is used instead,
    which keeps this function easy to exercise directly in tests.
    """
    players_df = validate_players_df(players_df if players_df is not None else load_players())
    forward_df = validate_stats_df(forward_df if forward_df is not None else load_stats("F"), "forwards CSV")
    defense_df = validate_stats_df(defense_df if defense_df is not None else load_stats("D"), "defencemen CSV")
    goalie_df = validate_stats_df(goalie_df if goalie_df is not None else load_stats("G"), "goalies CSV")

    year = detect_draft_year(forward_df, defense_df, goalie_df)

    forward_df = forward_df[forward_df["year"] == year].copy()
    defense_df = defense_df[defense_df["year"] == year].copy()
    goalie_df = goalie_df[goalie_df["year"] == year].copy()

    conn = db_connection()
    try:
        conn.execute("DELETE FROM player_stats")
        conn.execute("DELETE FROM player_status")
        conn.execute("DELETE FROM players")

        for row in players_df.itertuples(index=False):
            player_id = int(row.id)
            selected_raw = getattr(row, "selected", 0)
            selected_value = 0 if pd.isna(selected_raw) else int(selected_raw)
            conn.execute(
                "INSERT INTO players (id, name, position, selected, imported_year) VALUES (?, ?, ?, ?, ?)",
                (
                    player_id,
                    str(row.name),
                    str(row.position).upper(),
                    selected_value,
                    int(year),
                ),
            )
            conn.execute(
                "INSERT INTO player_status (player_id, status, notes) VALUES (?, 'available', '')",
                (player_id,),
            )

        for position, frame in {"F": forward_df, "D": defense_df, "G": goalie_df}.items():
            for row in frame.itertuples(index=False):
                row_data = row._asdict()
                payload = {key: value for key, value in row_data.items() if key != "id"}
                conn.execute(
                    "INSERT INTO player_stats (player_id, year, stats_type, position, data_json) VALUES (?, ?, ?, ?, ?)",
                    (
                        int(row_data["id"]),
                        int(year),
                        str(row_data["stats_type"]),
                        position,
                        json.dumps(payload, default=str),
                    ),
                )

        conn.execute(
            "INSERT INTO workspace_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("current_year", str(year)),
        )
        conn.execute(
            "INSERT INTO workspace_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("last_imported_at", str(pd.Timestamp.utcnow().isoformat())),
        )
        conn.commit()
        return {"players_imported": len(players_df), "year": int(year)}
    finally:
        conn.close()


def get_players_for_grid() -> pd.DataFrame:
    """Return a DataFrame for the dashboard confirming the imported players and their status."""
    conn = db_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.position, COALESCE(ps.status, 'available') AS status, p.imported_year
            FROM players p
            LEFT JOIN player_status ps ON ps.player_id = p.id
            ORDER BY p.name ASC
            """
        ).fetchall()
        data = [dict(row) for row in rows]
        return pd.DataFrame(data, columns=["id", "name", "position", "status", "imported_year"])
    finally:
        conn.close()


def get_workspace_summary() -> dict[str, str | int]:
    conn = db_connection()
    try:
        total_players = conn.execute("SELECT COUNT(*) AS count FROM players").fetchone()["count"]
        current_year = get_workspace_value("current_year")
        imported_at = get_workspace_value("last_imported_at")
        return {
            "total_players": int(total_players),
            "current_year": int(current_year) if current_year and current_year != "0" else 0,
            "last_imported_at": imported_at,
        }
    finally:
        conn.close()
