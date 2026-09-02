# Page: Player stats table

- **Menu position:** 6
- **Route:** `/player-stats-table`
- **Module:** `src/pages/player_stats_table.py`
- **Tests:** `tests/pages/player_stats_table/`
- **Status:** Implemented

## Purpose

Inspect the complete imported stat history for one player without draft-status,
roster, notes, or tag metadata.

## UI and behavior

- The searchable player picker includes every player currently stored in the
  workspace, regardless of position or draft state.
- Selecting a player generates an AG Grid table from that player's stored
  `player_stats` rows.
- Each row represents one `year` and `stats_type` (`projected` or `actual`)
  dataset. The remaining columns are dynamically derived from the selected
  player's available stat names.
- Stat names are displayed exactly as they are stored in the database. No
  skater/goalie schema is hard-coded and missing values remain blank.
- Clearing the player selection restores the empty table structure.

## Related code

- `src/pages/player_stats_table.py` — lookup, dynamic table shaping, and callback
- `src/storage.py` — player lookup and long-format stat-history access
