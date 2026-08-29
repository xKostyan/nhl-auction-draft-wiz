"""Shared pytest fixtures and test bootstrapping.

Building the Dash app here, at conftest module-import time (before any test
module in this tree is collected), is required because `src/pages/*` modules
call `dash.register_page(...)` as an import-time side effect, and Dash only
allows that after a `Dash(use_pages=True, ...)` app has already been created.
Individual test files can then safely `import src.pages.<page>` at module
level, or call `build_dashboard()` again to get a fresh app instance.
"""

from __future__ import annotations

import base64

import pandas as pd
import pytest

from src.dashboard import build_dashboard

# Build once, eagerly, so page modules can be imported by any test file below.
build_dashboard()


@pytest.fixture
def dash_app():
    """A freshly-built app instance (page registration is a no-op after the first call)."""
    return build_dashboard()


@pytest.fixture
def csv_data_url():
    """Return a helper that encodes a DataFrame as a Dash `dcc.Upload` contents payload."""

    def _make(df: pd.DataFrame) -> str:
        encoded = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode()
        return f"data:text/csv;base64,{encoded}"

    return _make


@pytest.fixture
def collect_component_ids():
    """Return a helper that recursively collects every component `id` in a layout tree."""

    def _collect(component) -> set[str]:
        ids: set[str] = set()
        component_id = getattr(component, "id", None)
        if isinstance(component_id, str):
            ids.add(component_id)

        children = getattr(component, "children", None)
        if children is None:
            return ids
        if isinstance(children, (list, tuple)):
            for child in children:
                ids |= _collect(child)
        elif hasattr(children, "id") or hasattr(children, "children"):
            ids |= _collect(children)
        return ids

    return _collect


@pytest.fixture
def walk_components():
    """Return a helper that yields every component in a layout tree, depth-first."""

    def _walk(component):
        yield component
        children = getattr(component, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                yield from _walk(child)
        elif children is not None and (hasattr(children, "id") or hasattr(children, "children")):
            yield from _walk(children)

    return _walk
