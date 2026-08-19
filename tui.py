# tui.py

import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Static, Log, Label
from textual.theme import Theme
from bcccheck import BCChecker

class BCCheckApp(App):
    """
    A minimalist, integrated Bandcamp YUM code checker TUI.
    Aesthetic: Catppuccin Mocha / "Blip_Blip" style.
    """
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "start", "Start Checking"),
        ("t", "cycle_theme", "Cycle Theme"),
    ]
    DEFAULT_THEME = "ansi-dark"

    def compose(self) -> ComposeResult:
        # Title bar without the pink background
        yield Label(" ═══ BCCCHECK ═══ ", id="app-title")
        with Container(id="main-container"):
            with Vertical(id="code-list-pane", classes="pane"):
                # DataTable for codes on the left
                yield DataTable()
            with Vertical(id="status-pane", classes="pane"):
                # Scrolling log on the right
                yield Log()
                # Status area at the bottom
                with Static(id="progress-area"):
                    yield Label("Press [bold blue]S[/] to start • [bold blue]Q[/] to quit", id="status-label")

    def on_mount(self) -> None:
        """Initialize themes and the data table with codes from file."""
        for _theme in THEMES:
            self.register_theme(_theme)
        start = getattr(self, "start_theme", None)
        self.theme = start if start in THEME_ORDER else "ansi-dark"

        table = self.query_one(DataTable)
        # Use explicit keys to avoid any look-up errors
        table.add_column("Code", key="code_col")
        table.add_column("Status", key="status_final")
        
        checker = BCChecker()
        codes = checker.load_codes()
        for code in codes:
            # We use the code as the row key for easy reference
            table.add_row(code, "Ready", key=code)
        
        self.log_msg("Ready. Press 's' to start.")

    def log_msg(self, msg: str) -> None:
        self.query_one(Log).write_line(f"» {msg}")

    async def action_start(self) -> None:
        """Handle the 's' key to start the checking process."""
        self.query_one("#status-label").update("[bold secondary]RUNNING...[/]")
        self.log_msg("Starting Playwright worker...")
        # Run the checker in a worker to keep the TUI responsive
        self.run_worker(self.check_process(), thread=False)

    def action_cycle_theme(self) -> None:
        """Cycle through the available themes with the 't' key."""
        try:
            idx = THEME_ORDER.index(self.theme)
        except ValueError:
            idx = -1
        next_theme = THEME_ORDER[(idx + 1) % len(THEME_ORDER)]
        self.theme = next_theme
        self.log_msg(f"Theme: {next_theme}")

    async def check_process(self) -> None:
        """Core logic for checking codes and updating the TUI."""
        checker = BCChecker(headless=False)
        
        async def ui_callback(msg, code=None, status=None):
            self.log_msg(msg)
            if code and status:
                table = self.query_one(DataTable)
                # Map internal status to a stylized string
                status_map = {
                    "checking": "[secondary]Checking...[/]",
                    "success": "[success]SUCCESS[/]",
                    "failed": "[warning]Invalid[/]",
                    "error": "[error]ERROR[/]"
                }
                
                try:
                    # Explicitly update the specific cell using the 'status_final' key
                    table.update_cell(code, "status_final", status_map.get(status, status))
                    # Move cursor to follow progress
                    table.move_cursor(row=table.get_row_index(code))
                except Exception as e:
                    # Fail silently in the UI if there's a minor cell mismatch
                    pass

        checker.on_update = ui_callback
        await checker.run()
        
        self.query_one("#status-label").update("[bold success]FINISHED[/]")
        self.log_msg("All codes checked.")

THEME_ORDER = ["ansi-dark", "dracula", "tokyo-night", "rose-pine"]

THEMES = [
    Theme(
        name="dracula",
        dark=True,
        background="#282a36",
        surface="#21222c",
        panel="#21222c",
        primary="#bd93f9",
        secondary="#8be9fd",
        accent="#50fa7b",
        success="#50fa7b",
        warning="#f1fa8c",
        error="#ff5555",
        foreground="#f8f8f2",
    ),
    Theme(
        name="tokyo-night",
        dark=True,
        background="#1a1b26",
        surface="#16161e",
        panel="#1f2335",
        primary="#7aa2f7",
        secondary="#bb9af7",
        accent="#7dcfff",
        success="#9ece6a",
        warning="#e0af68",
        error="#f7768e",
        foreground="#c0caf5",
    ),
    Theme(
        name="rose-pine",
        dark=False,
        background="#faf4ed",
        surface="#fffaf3",
        panel="#f2e9e1",
        primary="#907aa9",
        secondary="#56949f",
        accent="#d7827e",
        success="#84a07c",
        warning="#dfa47a",
        error="#b4637a",
        foreground="#575279",
    ),
]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="bcccheck TUI")
    parser.add_argument("--theme", help="Theme name: ansi-dark, dracula, tokyo-night, rose-pine")
    args = parser.parse_args()
    app = BCCheckApp()
    if args.theme:
        app.start_theme = args.theme
    app.run()
