# Support Multiple `--author` Values for `poetry init`

- **Repo:** python-poetry/poetry
- **Issue:** [#8864](https://github.com/python-poetry/poetry/issues/8864) — `poetry init --author` doesn't seem to allow multiple authors on Windows
- **PR:** [#10889](https://github.com/python-poetry/poetry/pull/10889)
- **Date:** 2026-05-10

## Problem

`poetry init --author "A <a>" --author "B <b>"` ignores all but the last `--author` value because the option is defined without `multiple=True`.

## Root Cause

In `src/poetry/console/commands/init.py`:

```python
click.option("--author", ...)  # no multiple=True
```

The `Layout` class also takes `author: str | None` — a single string — so even if the CLI passed multiple values, `generate_project_content()` would only output one.

## Fix

**Files modified:**

| File | Change |
|------|--------|
| `src/poetry/console/commands/init.py` | `--author` → `multiple=True`; `_init_pyproject()` handles `list[str]` |
| `src/poetry/layouts/layout.py` | `author: str | None` → `authors: list[str]`; iterate in template |
| `tests/conftest.py` | Update Layout constructor call |
| New test | `test_predefined_multiple_authors` |

**CLI change:**
```python
@click.option("--author", "authors", multiple=True, ...)
def _init_pyproject(self, ..., authors: tuple[str, ...]):
    ...
```

**Layout change:**
```python
class Layout:
    def __init__(self, ..., authors: list[str] | None = None):
        self._authors = authors or []
```

Added interactive loop: after initial author input, asks "Do you want to add another author?".

## CI Note

Poetry's CI was failing with "runner lost communication" — this was a GitHub Actions infrastructure issue, not related to the code changes.

## Key Insight

- Use `multiple=True` on click options for repeated values, not separate `--author` / `--authors` flags
- When changing a parameter from scalar to list, update ALL callers including test fixtures and `conftest.py`
- Interactive mode should loop: ask → append → confirm → repeat

## Keywords

`click` `multiple=True` `CLI` `tuple` `scalar to list` `conftest` `fixtures` `interactive` `poetry` `pyproject.toml` `author`
