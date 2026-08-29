from __future__ import annotations

import pandas as pd


def rank_players(players: pd.DataFrame, stats: pd.DataFrame, position: str | None = None) -> pd.DataFrame:
    """Create a draft-friendly ranked view for the selected position."""
    merged = players.merge(stats, on="id", how="left")
    if position:
        merged = merged[merged["position"] == position]

    projected = merged[merged["stats_type"] == "projected"].copy()
    actual = merged[merged["stats_type"] == "actual"].copy()

    if projected.empty or actual.empty:
        return projected if not projected.empty else actual

    projected = projected.sort_values(["FP_AVG", "FP"], ascending=False).reset_index(drop=True)
    actual = actual.sort_values(["FP_AVG", "FP"], ascending=False).reset_index(drop=True)

    projected["rank"] = range(1, len(projected) + 1)
    actual["rank"] = range(1, len(actual) + 1)
    return projected, actual
