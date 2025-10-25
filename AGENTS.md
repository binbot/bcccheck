# AGENTS.md - bcccheck

## Commands
- **Run**: `python bcccheck.py`
- **Install deps**: `pip install -r requirements.txt && playwright install`
- **Build standalone**: `pip install pyinstaller && pyinstaller bcccheck.spec`
- **No tests defined** - add pytest if needed: `pytest` (single test: `pytest test_file.py::test_name`)

## Code Style
- **Imports**: stdlib first, then third-party (pathlib, asyncio, sys, playwright)
- **Naming**: snake_case functions, UPPER_CASE constants, camelCase selectors dict
- **Types**: Minimal type hints (add for new functions)
- **Error handling**: try/except with pass for non-critical errors
- **Formatting**: 4-space indent, single quotes for strings, f-strings for formatting
- **Structure**: Async functions, no classes, constants at top
- **Comments**: Minimal, only for complex logic