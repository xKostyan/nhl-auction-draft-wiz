from __future__ import annotations

import base64
import csv
import io
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "csv-src-import-examples"

REQUIRED_PLAYER_COLUMNS = {"id", "name", "position"}
REQUIRED_STATS_COLUMNS = {"id", "year", "stats_type"}
KEEPER_PRICE_COLUMNS = ["name", "position", "team", "price"]


def _read_csv_bytes(data: bytes) -> pd.DataFrame:
    """Parse CSV bytes trying encodings the yearly export is known to use."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(data), encoding="latin-1")


def _read_csv(path: Path) -> pd.DataFrame:
    """Read repo CSV fixtures using a compatible encoding for the sample data."""
    return _read_csv_bytes(path.read_bytes())


def parse_uploaded_csv(contents: str) -> pd.DataFrame:
    """Decode a Dash `dcc.Upload` `contents` payload (data URL) into a DataFrame."""
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)
    return _read_csv_bytes(decoded)


def parse_uploaded_keeper_prices(contents: str) -> pd.DataFrame:
    """Decode the headerless keeper-price export into normalized columns.

    Each row contains a quoted ``name, position, team`` value and a dollar
    amount. The exported positions LW/RW/C are normalized to the workspace's
    ``F`` position so price matching uses the same position codes as players.
    """
    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("Keeper prices CSV could not be decoded.") from exc

    try:
        csv_text = decoded.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Mac Roman is used by the keeper-price export; e.g. 0x9f is "ü".
        csv_text = decoded.decode("mac_roman")

    position_map = {"LW": "F", "RW": "F", "C": "F", "D": "D", "G": "G"}
    rows: list[dict[str, str | int]] = []
    for line_number, row in enumerate(csv.reader(io.StringIO(csv_text)), start=1):
        if not row:
            continue
        if len(row) != 2:
            raise ValueError(
                f"Keeper prices CSV line {line_number} must contain exactly two cells."
            )

        identity, raw_price = row
        identity_parts = [part.strip() for part in identity.rsplit(",", 2)]
        if len(identity_parts) != 3 or not all(identity_parts):
            raise ValueError(
                f"Keeper prices CSV line {line_number} must use 'player name, position, team'."
            )
        name, raw_position, team = identity_parts
        position = position_map.get(raw_position.upper())
        if position is None:
            raise ValueError(
                f"Keeper prices CSV line {line_number} has unsupported position {raw_position!r}."
            )

        price_text = raw_price.strip()
        if not price_text.startswith("$") or not price_text[1:].isdecimal():
            raise ValueError(
                f"Keeper prices CSV line {line_number} must contain a non-negative whole-dollar price."
            )
        rows.append(
            {"name": name, "position": position, "team": team, "price": int(price_text[1:])}
        )

    if not rows:
        raise ValueError("Keeper prices CSV has no data rows.")
    return pd.DataFrame(rows, columns=KEEPER_PRICE_COLUMNS)


def validate_players_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a players dataset has the columns the workspace requires."""
    missing = REQUIRED_PLAYER_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"players CSV is missing required columns: {sorted(missing)}")
    return df


def validate_stats_df(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Ensure a position stats dataset has the columns the workspace requires."""
    missing = REQUIRED_STATS_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"{label} is missing required columns: {sorted(missing)}")
    return df


def load_players() -> pd.DataFrame:
    """Load the bundled sample players CSV and normalize required fields."""
    return validate_players_df(_read_csv(CSV_DIR / "players.csv"))


def load_stats(position: str) -> pd.DataFrame:
    """Load the bundled sample stats CSV for a position, e.g. F, D, or G."""
    key_map = {"F": "f_stats.csv", "D": "d_stats.csv", "G": "g_stats.csv"}
    file_name = key_map.get(position.upper())
    if file_name is None:
        raise ValueError(f"Unsupported position: {position!r}. Expected one of F, D, G.")

    return validate_stats_df(_read_csv(CSV_DIR / file_name), file_name)
