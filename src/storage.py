from __future__ import annotations

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
    """Create the schema for persistent player/workspace state.

    `player_stats` stores every (year, stats_type, stat_name) data point for every
    player as its own row (an "EAV" long format), rather than only the upcoming
    draft season. This keeps the full multi-year projected-vs-actual history
    available for later historical analysis features, while remaining simple to
    query for a single year/stat at a time.
    """
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
                current_season INTEGER NOT NULL,
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
                stat_name TEXT NOT NULL,
                stat_value REAL,
                PRIMARY KEY (player_id, year, stats_type, stat_name),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_player_stats_lookup ON player_stats (player_id, year, stats_type)"
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO workspace_meta (key, value) VALUES
                ('workspace_name', 'default'),
                ('current_season', '0'),
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
                ("current_season", "0"),
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


def _stats_frame_to_rows(frame: pd.DataFrame, position: str) -> list[tuple]:
    """Flatten a wide position stats DataFrame into long (player, year, type, stat) rows.

    Every year and every stats_type present in the source file is kept (not just
    the current draft season), so the workspace retains the full historical
    projected-vs-actual record for each player. Empty/NaN values are skipped since
    they represent data that doesn't exist yet (e.g. 'actual' for a future season).
    """
    stat_columns = [c for c in frame.columns if c not in ("id", "year", "stats_type")]
    if not stat_columns:
        return []

    melted = frame.melt(
        id_vars=["id", "year", "stats_type"],
        value_vars=stat_columns,
        var_name="stat_name",
        value_name="stat_value",
    )
    melted = melted.dropna(subset=["stat_value"])

    return [
        (int(player_id), int(year), str(stats_type), position, str(stat_name), float(stat_value))
        for player_id, year, stats_type, stat_name, stat_value in melted[
            ["id", "year", "stats_type", "stat_name", "stat_value"]
        ].itertuples(index=False, name=None)
    ]


def import_yearly_dataset(
    players_df: pd.DataFrame | None = None,
    forward_df: pd.DataFrame | None = None,
    defense_df: pd.DataFrame | None = None,
    goalie_df: pd.DataFrame | None = None,
) -> dict[str, int]:
    """Import the four expected CSV datasets into the local SQLite workspace.

    This replaces any existing dataset and stores every year and every
    projected/actual data point found in the stats files, so historical analysis
    across seasons remains possible later. The current draft season (used to tag
    `players.current_season`) is detected automatically as the year with only
    projected, no actual, data yet. When a dataset is omitted, the bundled sample
    CSV fixture is used instead, which keeps this function easy to exercise
    directly in tests.
    """
    players_df = validate_players_df(players_df if players_df is not None else load_players())
    forward_df = validate_stats_df(forward_df if forward_df is not None else load_stats("F"), "forwards CSV")
    defense_df = validate_stats_df(defense_df if defense_df is not None else load_stats("D"), "defencemen CSV")
    goalie_df = validate_stats_df(goalie_df if goalie_df is not None else load_stats("G"), "goalies CSV")

    draft_season = detect_draft_year(forward_df, defense_df, goalie_df)

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
                "INSERT INTO players (id, name, position, selected, current_season) VALUES (?, ?, ?, ?, ?)",
                (
                    player_id,
                    str(row.name),
                    str(row.position).upper(),
                    selected_value,
                    int(draft_season),
                ),
            )
            conn.execute(
                "INSERT INTO player_status (player_id, status, notes) VALUES (?, 'available', '')",
                (player_id,),
            )

        stat_rows_imported = 0
        for position, frame in {"F": forward_df, "D": defense_df, "G": goalie_df}.items():
            rows = _stats_frame_to_rows(frame, position)
            if rows:
                conn.executemany(
                    """
                    INSERT INTO player_stats (player_id, year, stats_type, position, stat_name, stat_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                stat_rows_imported += len(rows)

        conn.execute(
            "INSERT INTO workspace_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("current_season", str(draft_season)),
        )
        conn.execute(
            "INSERT INTO workspace_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("last_imported_at", str(pd.Timestamp.utcnow().isoformat())),
        )
        conn.commit()
        return {
            "players_imported": len(players_df),
            "year": int(draft_season),
            "stat_rows_imported": stat_rows_imported,
        }
    finally:
        conn.close()


def get_players_for_grid() -> pd.DataFrame:
    """Return a DataFrame for the dashboard confirming the imported players and their status."""
    conn = db_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.position, COALESCE(ps.status, 'available') AS status, p.current_season
            FROM players p
            LEFT JOIN player_status ps ON ps.player_id = p.id
            ORDER BY p.name ASC
            """
        ).fetchall()
        data = [dict(row) for row in rows]
        return pd.DataFrame(data, columns=["id", "name", "position", "status", "current_season"])
    finally:
        conn.close()


def get_players_for_position_grid(position: str) -> pd.DataFrame:
    """Return one position's players for the live draft table.

    The player id remains in the row data so a status edit can be persisted,
    but position pages deliberately do not render it as a visible column.
    """
    normalized_position = position.upper()
    if normalized_position not in {"F", "D", "G"}:
        raise ValueError(f"Unsupported position: {position!r}. Expected F, D, or G.")

    conn = db_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, CASE WHEN ps.status = 'drafted' THEN 1 ELSE 0 END AS drafted
            FROM players p
            LEFT JOIN player_status ps ON ps.player_id = p.id
            WHERE p.position = ?
            ORDER BY p.name ASC
            """,
            (normalized_position,),
        ).fetchall()
        data = [
            {"id": int(row["id"]), "name": row["name"], "drafted": bool(row["drafted"])}
            for row in rows
        ]
        return pd.DataFrame(data, columns=["id", "name", "drafted"])
    finally:
        conn.close()


def set_player_drafted(player_id: int, drafted: bool) -> None:
    """Persist whether a player has been drafted during the live auction."""
    status = "drafted" if drafted else "available"
    conn = db_connection()
    try:
        player = conn.execute("SELECT id FROM players WHERE id = ?", (player_id,)).fetchone()
        if player is None:
            raise ValueError(f"Cannot update drafted status: player {player_id} does not exist.")

        conn.execute("UPDATE players SET selected = ? WHERE id = ?", (int(drafted), player_id))
        conn.execute(
            """
            INSERT INTO player_status (player_id, status, notes)
            VALUES (?, ?, '')
            ON CONFLICT(player_id) DO UPDATE SET
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (player_id, status),
        )
        conn.commit()
    finally:
        conn.close()


def get_player_stat_history(player_id: int) -> pd.DataFrame:
    """Return the full imported stat history for one player in long format.

    Columns: year, stats_type, stat_name, stat_value. Every imported year and
    both 'projected' and 'actual' stats_type values are included (subject to
    what data existed in the source CSVs), which supports year-over-year and
    projected-vs-actual comparisons for a single player.
    """
    conn = db_connection()
    try:
        rows = conn.execute(
            """
            SELECT year, stats_type, stat_name, stat_value
            FROM player_stats
            WHERE player_id = ?
            ORDER BY year ASC, stats_type ASC, stat_name ASC
            """,
            (player_id,),
        ).fetchall()
        data = [dict(row) for row in rows]
        return pd.DataFrame(data, columns=["year", "stats_type", "stat_name", "stat_value"])
    finally:
        conn.close()


def get_available_stat_years() -> list[int]:
    """Return the sorted list of years currently stored in the workspace's stat history."""
    conn = db_connection()
    try:
        rows = conn.execute("SELECT DISTINCT year FROM player_stats ORDER BY year ASC").fetchall()
        return [int(row["year"]) for row in rows]
    finally:
        conn.close()


def get_workspace_summary() -> dict[str, str | int]:
    conn = db_connection()
    try:
        total_players = conn.execute("SELECT COUNT(*) AS count FROM players").fetchone()["count"]
        total_stat_rows = conn.execute("SELECT COUNT(*) AS count FROM player_stats").fetchone()["count"]
        current_season = get_workspace_value("current_season")
        imported_at = get_workspace_value("last_imported_at")
        return {
            "total_players": int(total_players),
            "total_stat_rows": int(total_stat_rows),
            "current_season": int(current_season) if current_season and current_season != "0" else 0,
            "last_imported_at": imported_at,
        }
    finally:
        conn.close()
