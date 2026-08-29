from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from .data_loader import CSV_DIR, load_players, load_stats

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


def import_yearly_dataset(
    year: int,
    players_path: str | Path | None = None,
    forward_path: str | Path | None = None,
    defense_path: str | Path | None = None,
    goalie_path: str | Path | None = None,
) -> int:
    """Import a season dataset into the local SQLite workspace.

    This replaces the current dataset so the app can track draft availability and keepers
    against a fresh yearly import.
    """
    players_df = load_players() if players_path is None else pd.read_csv(players_path, encoding="latin-1")
    forward_df = (load_stats("F") if forward_path is None else pd.read_csv(forward_path, encoding="latin-1")).copy()
    defense_df = (load_stats("D") if defense_path is None else pd.read_csv(defense_path, encoding="latin-1")).copy()
    goalie_df = (load_stats("G") if goalie_path is None else pd.read_csv(goalie_path, encoding="latin-1")).copy()

    for frame in (forward_df, defense_df, goalie_df):
        if "year" in frame.columns:
            frame.drop(frame[frame["year"] != int(year)].index, inplace=True)

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
        return len(players_df)
    finally:
        conn.close()


def set_player_status(player_id: int, status: str, notes: str = "") -> None:
    """Set the tracking status for an imported player (available, drafted, keeper, unavailable)."""
    allowed = {"available", "drafted", "keeper", "unavailable"}
    if status not in allowed:
        raise ValueError(f"Unsupported player status: {status!r}")

    conn = db_connection()
    try:
        conn.execute(
            """
            INSERT INTO player_status (player_id, status, notes, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(player_id) DO UPDATE SET
                status = excluded.status,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
            """,
            (player_id, status, notes),
        )
        conn.commit()
    finally:
        conn.close()


def get_player_status(player_id: int) -> str:
    conn = db_connection()
    try:
        row = conn.execute(
            "SELECT status FROM player_status WHERE player_id = ?",
            (player_id,),
        ).fetchone()
        return row["status"] if row else "available"
    finally:
        conn.close()


def get_players_for_grid() -> pd.DataFrame:
    """Return a DataFrame for the dashboard with each player's status."""
    conn = db_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.position, p.selected, COALESCE(ps.status, 'available') AS status,
                   COALESCE(ps.notes, '') AS notes, p.imported_year
            FROM players p
            LEFT JOIN player_status ps ON ps.player_id = p.id
            ORDER BY p.name ASC
            """
        ).fetchall()
        data = [dict(row) for row in rows]
        return pd.DataFrame(data)
    finally:
        conn.close()


def get_workspace_summary() -> dict[str, str | int]:
    conn = db_connection()
    try:
        total_players = conn.execute("SELECT COUNT(*) AS count FROM players").fetchone()["count"]
        drafted = conn.execute("SELECT COUNT(*) AS count FROM player_status WHERE status = 'drafted'").fetchone()["count"]
        keepers = conn.execute("SELECT COUNT(*) AS count FROM player_status WHERE status = 'keeper'").fetchone()["count"]
        current_year = get_workspace_value("current_year")
        imported_at = get_workspace_value("last_imported_at")
        return {
            "total_players": int(total_players),
            "drafted": int(drafted),
            "keepers": int(keepers),
            "current_year": int(current_year) if current_year and current_year != "0" else 0,
            "last_imported_at": imported_at,
        }
    finally:
        conn.close()


def load_latest_workspace() -> pd.DataFrame:
    """Convenience wrapper for the Dashboard: return the current local workspace state."""
    if not (DEFAULT_DB_PATH.exists() if _DB_PATH == DEFAULT_DB_PATH else Path(_DB_PATH).exists()):
        ensure_schema()
    return get_players_for_grid()
