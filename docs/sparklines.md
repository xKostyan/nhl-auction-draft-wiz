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
