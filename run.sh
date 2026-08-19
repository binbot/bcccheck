#!/usr/bin/env bash
# Launch the bcccheck TUI. `uv run` auto-installs dependencies into a managed
# virtual environment, so there is no need to create a .venv by hand.
set -euo pipefail
uv run tui.py "$@"
