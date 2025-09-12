from textual import reactive
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import var
from textual.widgets import Header, Static
from textual.command import Hit, Hits, Provider
from textual.screen import Screen

from functools import partial
from collections.abc import Iterable

import datetime as dt

from .config import AppConfig
from .journal import JournalPane
from .stats import StatsPane
from .footer import Footer

class JournalSarApp(App):
    """Main application class for the Journal+SAR TUI."""

    CSS_PATH="sar_journal.tcss"

    BINDINGS = (
        [
            Binding("q", "quit", "Quit"),
            Binding("r", "reload", "Reload", tooltip='Reload statistics and journal'),
            # Metric switching
            Binding("c", "metric('cpu')", "CPU"),
            Binding("l", "metric('load')", "Load"),
            Binding("m", "metric('mem')", "Mem"),
            Binding("d", "metric('disk')", "Disk"),
            Binding("n", "metric('net')", "Net"),
        ]
        + [Binding(str(n), f"prio({n})", f"Prio≤{n}") for n in range(8)]
        + [
            Binding("b", "shift_time(-10)", "Back 10m"),
            Binding("f", "shift_time(10)", "Forward 10m", tooltip="Go 10m forward in Time"),
        ]
    )

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, cfg: AppConfig):
        """Initialize the application."""
        super().__init__()
        self.cfg = cfg
        self.journal = JournalPane(cfg)
        self.journal.id = "journal"
        self.stats = StatsPane(cfg)
        self.stats.id = "stats"
        self._shift_direction = -1 # Default to shifting backward

    def on_mount(self) -> None:
        """Called when the app is mounted. Triggers initial data load."""
        self.action_reload()

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        with Vertical():
            yield self.stats
            yield self.journal
            yield Footer()

    def action_reload(self) -> None:
        """Action to reload both journal entries and statistics."""
        self.journal.reload()
        found_data = self.stats.load_metric(self.stats.metric)
        # If no data is found, shift time until data appears
        if not found_data:
            i: int = 0
            while not found_data and i < 100:
                i += 1
                self.cfg.time += dt.timedelta(minutes=self._shift_direction * 10)
                self.cfg.until += dt.timedelta(minutes=self._shift_direction * 10)
                self.log(f"No data, shifting time to {self.cfg.time}")
                found_data = self.stats.load_metric(self.stats.metric)

    def action_metric(self, which: str) -> None:
        """Action to switch to a different metric type."""
        self.stats.set_metric(which)

    def action_prio(self, level: int) -> None:
        """Action to set journal priority filter level."""
        self.journal.set_prio(level)

    def action_shift_time(self, minutes: int) -> None:
        """Shift the time window by the given number of minutes."""
        # Update shift direction if user explicitly goes forward or backward
        if minutes > 0:
            self._shift_direction = 1
        elif minutes < 0:
            self._shift_direction = -1

        if minutes > 0:
            now = dt.datetime.now().replace(microsecond=0)
            if self.cfg.time + dt.timedelta(minutes=minutes) > now:
                minutes = int((now - self.cfg.time).total_seconds() / 60)
                if minutes < 0: # Already past now
                    minutes = 0
        self.cfg.time += dt.timedelta(minutes=minutes)
        self.cfg.until += dt.timedelta(minutes=minutes)
        self.action_reload()

