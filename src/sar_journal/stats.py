import csv, subprocess, datetime as dt
from textual.widgets import Static, DataTable
from textual.reactive import reactive
from textual.app import ComposeResult
from .config import AppConfig
from .constants import STAT_PRESETS

class StatsPane(Static):
    """Widget for displaying system statistics from sysstat.
    
    This pane shows various system metrics (CPU, memory, disk, etc.) in tabular format
    using data from the sar/sar utilities.
    
    Attributes:
        metric: Reactive current metric type being displayed
    """
    metric = reactive("cpu")

    def __init__(self, cfg: AppConfig):
        """Initialize the stats pane.
        
        Args:
            cfg: Application configuration
            styles.height: Fixed height for the Stats Pane
        """
        super().__init__()
        self.cfg = cfg
        self.table = DataTable()
        self.styles.height = 8


    def compose(self) -> ComposeResult:
        """Compose the stats pane layout.
        
        Yields:
            Static header with current metric name
            DataTable for displaying metric data
        """
        yield Static(f"SAR {self.metric}")
        yield self.table

    def set_metric(self, metric: str) -> None:
        """Set the current metric type and reload data.
        
        Args:
            metric: Metric type key (must exist in STAT_PRESETS)
        """
        if metric not in STAT_PRESETS:
            return
        self.metric = metric
        self.load_metric(metric)

    def load_metric(self, metric: str) -> None:
        """Load and display system statistics for the given metric.

        Invokes the ``sar`` command with the configured start and end times
        and the metric-specific options from ``STAT_PRESETS``. The output is
        parsed and displayed in the table widget.

        Args:
            metric (str): Key identifying which metric to load, as defined
            in ``STAT_PRESETS``.
    
        Side Effects:
            Clears and repopulates ``self.table`` with the retrieved data.
        """
        self.table.clear(columns=True)
        now = dt.datetime.now()
        delta_days = (now.date() - self.cfg.time.date()).days
        start_time = self.cfg.time - dt.timedelta(minutes=10)
        end_time = self.cfg.until + dt.timedelta(minutes=1)
        cmd = [
            "sar",
            "-" + str(delta_days),
            "-s", start_time.strftime("%H:%M:%S"),
            "-e", end_time.strftime("%H:%M:%S"),
        ] + STAT_PRESETS[metric]["sar_opts"]

        
        try:
            out = subprocess.check_output(cmd, text=True)
        except Exception as e:
            self.table.add_column("Error")
            self.table.add_row(str(e))
            return
            
        rows = list(csv.reader(out.splitlines(), delimiter=';'))
        if not rows:
            self.table.add_column("Status")
            self.table.add_row("No data available")
            return
            
        # Add columns from header row
        header = rows[0]
        self.table.add_columns(*header)
        
        # Add data rows (limit to 50 for performance)
        for row in rows[1:50]:
            # Ensure row has same number of columns as header
            padded_row = row + [''] * (len(header) - len(row))
            self.table.add_row(*padded_row[:len(header)])
