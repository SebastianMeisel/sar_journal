from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Header, Footer
from textual.command import Command
import datetime as dt
from .config import AppConfig
from .journal import JournalPane
from .stats import StatsPane
from collections.abc import Iterable

class JournalSarApp(App):
    """Main application class for the Journal+SAR TUI.
    
    This application provides a split-pane interface showing Linux journal entries
    on the left and system statistics on the right. Users can filter journal entries
    by priority and switch between different metric types.
    """
    
    CSS = """
    Horizontal { height: 1fr; }
    #journal, #stats { width: 1fr; min-width: 40; }
    Log { 
        text-wrap: wrap;
    }
    DataTable { 
        scrollbar-size: 1 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reload", "Reload"),
        # Metric switching
        Binding("c", "metric('cpu')",  "CPU"),
        Binding("l", "metric('load')", "Load"), 
        Binding("m", "metric('mem')",  "Mem"),
        Binding("d", "metric('disk')", "Disk"),
        Binding("n", "metric('net')",  "Net"),
    ] + [
        Binding(str(n), f"prio({n})", f"Prio≤{n}") for n in range(8)
    ] + [
        Binding("b", "shift_time(-10)", "Back 10m"),
        Binding("f", "shift_time(10)", "Forward 10m"),
    ]

    def __init__(self, cfg: AppConfig):
        """Initialize the application.
        
        Args:
            cfg: Application configuration
        """
        super().__init__()
        self.cfg = cfg
        self.journal = JournalPane(cfg)
        self.journal.id = "journal"
        self.stats = StatsPane(cfg)
        self.stats.id = "stats"

    def on_mount(self) -> None:
        """Called when the app is mounted. Triggers initial data load."""
        self.action_reload()



    def compose(self) -> ComposeResult:
        """Compose the main application layout.
           
           Yields:
           Header with application title and bindings
           Vertical container with journal (top, flexible)
           and stats (bottom, fixed 5 lines)
           Footer with key bindings
           """
        yield Header()
        with Vertical():
            yield self.stats
            yield self.journal
            yield Footer()

    def action_reload(self) -> None:
        """Action to reload both journal entries and statistics."""
        self.journal.reload()
        self.stats.load_metric(self.stats.metric)

    def action_metric(self, which: str) -> None:
        """Action to switch to a different metric type.
        
        Args:
            which: Metric type key from STAT_PRESETS
        """
        self.stats.set_metric(which)

    def action_prio(self, level: int) -> None:
        """Action to set journal priority filter level.
        
        Args:
            level: Maximum priority level to display (0-7)
        """
        self.journal.set_prio(level)

    def action_shift_time(self, minutes: int) -> None:
        """Shift the time window by the given number of minutes.
    
        Args:
            minutes: Positive to move forward, negative to move backward.
        """
        self.cfg.time += dt.timedelta(minutes=minutes)
        self.cfg.until += dt.timedelta(minutes=minutes)
        self.action_reload()

    def get_system_commands(self, screen):
        """Extend system commands with a custom 'show-pallet'."""
        yield from super().get_system_commands(screen)

        def show_pallet_callback() -> None:
            self.log("show-pallet command executed")
    
        # ✅ Use the 3-arg form: name, callback, help-text
        yield Command(
            "show-pallet",
            show_pallet_callback,
            "Show helpful information about sar_journal",
        )
