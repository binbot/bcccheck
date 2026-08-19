#!/usr/bin/env bash
# Launch the bcccheck TUI (macOS). Double-clicking a .command file runs it in
# Terminal. `uv run` auto-installs dependencies, so no manual .venv needed.
uv run tui.py "$@"
