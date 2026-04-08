# tui.py

import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Static, Log, Label
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
    ]

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
        """Initialize the data table with codes from file."""
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
        self.query_one("#status-label").update("[bold blue blink]RUNNING...[/]")
        self.log_msg("Starting Playwright worker...")
        # Run the checker in a worker to keep the TUI responsive
        self.run_worker(self.check_process(), thread=False)

    async def check_process(self) -> None:
        """Core logic for checking codes and updating the TUI."""
        checker = BCChecker(headless=False)
        
        async def ui_callback(msg, code=None, status=None):
            self.log_msg(msg)
            if code and status:
                table = self.query_one(DataTable)
                # Map internal status to a stylized string
                status_map = {
                    "checking": "[cyan]Checking...[/]",
                    "success": "[bold green]SUCCESS[/]",
                    "failed": "[grey50]Invalid[/]",
                    "error": "[bold red]ERROR[/]"
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
        
        self.query_one("#status-label").update("[bold green]FINISHED[/]")
        self.log_msg("All codes checked.")

if __name__ == "__main__":
    app = BCCheckApp()
    app.run()
