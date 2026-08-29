from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "csv-src-import-examples"


def _read_csv(path: Path) -> pd.DataFrame:
    """Read repo CSV fixtures using a compatible encoding for the sample data."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="latin-1")


def load_players() -> pd.DataFrame:
    """Load the players CSV and normalize required fields."""
    df = _read_csv(CSV_DIR / "players.csv")
    required = {"id", "name", "position"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"players.csv is missing required columns: {sorted(missing)}")
    return df


def load_stats(position: str) -> pd.DataFrame:
    """Load the stats CSV for a position, e.g. F, D, or G."""
    key_map = {"F": "f_stats.csv", "D": "d_stats.csv", "G": "g_stats.csv"}
    file_name = key_map.get(position.upper())
    if file_name is None:
        raise ValueError(f"Unsupported position: {position!r}. Expected one of F, D, G.")

    df = _read_csv(CSV_DIR / file_name)
    if "id" not in df.columns:
        raise ValueError(f"{file_name} is missing the required 'id' column.")
    return df


def load_player_data() -> dict[str, pd.DataFrame]:
    """Return a dict with the core CSV datasets used by the app."""
    return {
        "players": load_players(),
        "forwards": load_stats("F"),
        "defense": load_stats("D"),
        "goalies": load_stats("G"),
    }
