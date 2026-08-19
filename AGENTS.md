# AGENTS.md - bcccheck

## Commands
- **Run (TUI)**: `uv run tui.py` (or `./run.sh`)
- **Run (CLI)**: `uv run bcccheck.py --show-browser`
- **Install deps**: `uv sync` (or `pip install -r requirements.txt && playwright install chromium`)
- **Build standalone**: not currently configured (no `bcccheck.spec`); see binary plan.
- **Tests**: `pytest` (single test: `pytest test_file.py::test_name`)

## Code Style
- **Imports**: stdlib first, then third-party (pathlib, asyncio, sys, playwright)
- **Naming**: snake_case functions, UPPER_CASE constants, camelCase selectors dict
- **Types**: Minimal type hints (add for new functions)
- **Error handling**: try/except with logging for non-critical errors
- **Formatting**: 4-space indent, single quotes for strings, f-strings for formatting
- **Structure**: Class-based `BCChecker` plus async functions; constants at top
- **Comments**: Minimal, only for complex logic