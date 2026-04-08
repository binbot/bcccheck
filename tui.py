# tui.py

import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, DataTable, Static, Log, Label
from textual.worker import Worker, WorkerState
from bcccheck import BCChecker, CODES_FILE

class BCCheckApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "start", "Start Checking"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Vertical(id="code-list-pane", classes="pane"):
                yield Label("[bold cyan]CODES LIST[/]")
                yield DataTable()
            with Vertical(id="status-pane", classes="pane"):
                yield Label("[bold magenta]ACTIVITY LOG[/]")
                yield Log()
                with Static(id="progress-area"):
                    yield Label("Press [bold secondary]'s'[/] to start checking codes", id="status-label")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the data table with codes from file."""
        table = self.query_one(DataTable)
        # We explicitly name the column keys so we can find them later
        table.add_column("Code", key="code_col")
        table.add_column("Status", key="status_col")
        
        checker = BCChecker()
        codes = checker.load_codes()
        for code in codes:
            # We use the code itself as the unique 'key' for the row
            table.add_row(code, "Ready", key=code)
        
        self.log_msg("Ready. Press 's' to start.")

    def log_msg(self, msg: str) -> None:
        self.query_one(Log).write_line(f"» {msg}")

    async def action_start(self) -> None:
        """Handle the 's' key to start the checking process."""
        self.query_one("#status-label").update("[bold blink secondary]RUNNING...[/]")
        self.log_msg("Starting Playwright worker...")
        
        # We use a worker to keep the TUI responsive while Playwright runs
        self.run_worker(self.check_process(), thread=False)

    async def check_process(self) -> None:
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
                    # Update the specific cell using the explicit column key
                    table.update_cell(code, "status_col", status_map.get(status, status))
                    # Ensure the row is visible
                    table.move_cursor(row=table.get_row_index(code))
                except Exception as e:
                    self.log_msg(f"UI Error: {e}")

        checker.on_update = ui_callback
        await checker.run()
        
        self.query_one("#status-label").update("[bold accent]FINISHED[/]")
        self.log_msg("Checking process complete.")

if __name__ == "__main__":
    app = BCCheckApp()
    app.run()
