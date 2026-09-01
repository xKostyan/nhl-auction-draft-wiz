# Dash AG Grid inline sparklines

Use this pattern for compact, per-player visualizations inside AG Grid table
cells. It avoids creating a separate Dash or Plotly component for every row.

## Implementation

1. Shape the value in the storage helper as JSON-compatible row data. Keep the
   rendering data separate from visible display fields; for example,
   `actual_gp_history` is a list of `{"year": ..., "games_played": ...}`
   dictionaries.
2. Define the renderer in
   `src/assets/dashAgGridComponentFunctions.js`. Dash creates the app from
   `src/dashboard.py`, so its asset folder is `src/assets/`; a repository-root
   `assets/` directory is not served.
3. Register the renderer in
   `window.dashAgGridComponentFunctions`, not
   `window.dashAgGridFunctions`. The former is specifically for custom cell
   renderers; the latter is only for JavaScript function-valued grid options.
4. Return a React element using `React.createElement(...)`. Do not return raw
   DOM nodes from `document.createElement(...)`.
5. Reference the registered component by name in the column definition, such
   as `"cellRenderer": "actualGpSparkline"`. Do not wrap a cell renderer in a
   `{"function": ...}` expression.
6. Set `dangerously_allow_code=True` on the owning `dag.AgGrid` and test that
   Dash serves the component at
   `/assets/dashAgGridComponentFunctions.js`.

For new renderers, use inline styles or add styles to `src/assets/`, give
individual marks an accessible browser tooltip with `title`, and add focused
tests for the column definition, row-data shape, and renderer registration.

## Existing health chart

`actualGpSparkline` implements the skater **Health (actual GP)** column.
It accepts up to five historical actual-GP values and renders oldest to newest
on a fixed 0-84 scale. Its color bands are red for 0-50 GP, orange for 51-60,
yellow for 61-71, and green for 72-84.

## Existing goalie game-starts chart

`goalieGameStartsChart` implements the goalie **Game Starts** column. It
receives every imported goalie season, with absent projected or actual values
normalized to zero. It draws projected starts as a blue line and actual starts
as 0-70-scale bars with a 9px value label. Actual bars are red below 30 starts,
yellow from 30 through 42, and green above 42.

## Existing average-performance chart

`averagePerformanceChart` implements the **Average Performance** column on
every position page. It uses the same projected-line/actual-bar presentation
as the goalie game-starts chart, with absent values normalized to zero. The
fixed range is 0-6 for skaters and 0-12 for goalies. Skater actual bars are
red through 3.1, orange through 3.5, yellow through 3.9, and green above 3.9;
goalie actual bars are red below 7.0, orange through 7.5, yellow through 8.0,
and green above 8.0.
