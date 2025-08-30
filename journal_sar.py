#!/usr/bin/env python3
"""
Journal+SAR TUI
----------------
A Textual TUI showing Linux journal entries (via journalctl) and sysstat metrics (via sar).

This application provides a real-time monitoring interface that displays system journal
entries alongside system performance metrics from sysstat. It supports filtering journal
entries by priority level and switching between different metric types.

Keys:
  q quit
  r reload
  0..7 set journal max priority
  c    switch to CPU metrics
  l    switch to Load metrics
  m    switch to Memory metrics
  d    switch to Disk metrics
  n    switch to Network metrics
"""

import argparse
import csv
import datetime as dt
from datetime import timedelta

import shutil
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Log
from textual.reactive import reactive

# Journal priority level mappings
PRIO_NAMES = {
    0: "EMERG",
    1: "ALERT", 
    2: "CRIT",
    3: "ERR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFO",
    7: "DEBUG",
}

# Styling for different priority levels
PRIO_STYLES = {
    0: "bold white on red3",
    1: "bold white on dark_red",
    2: "bold red",
    3: "red3",
    4: "yellow3",
    5: "cyan",
    6: "white",
    7: "dim",
}

# SAR metric configurations
STAT_PRESETS = {
    "cpu": {"sar_opts": ["-u", "ALL"], "want": ["%user", "%system", "%iowait", "%idle"]},
    "load": {"sar_opts": ["-q"], "want": ["runq-sz", "ldavg-1", "ldavg-5"]},
    "mem": {"sar_opts": ["-r"], "want": ["kbmemfree", "kbmemused", "%memused"]},
    "disk": {"sar_opts": ["-b"], "want": ["tps", "rtps", "wtps"]},
    "net": {"sar_opts": ["-n", "DEV"], "want": ["IFACE", "rxpck/s", "txpck/s"]},
}

@dataclass
class AppConfig:
    """Configuration container for the application.
    
    Attributes:
        Time: Start datetime for data collection (10min samples)
        prio_max: Maximum priority level for journal entries (0-7)
        metric: Current metric type to display
        log_limit: Maximum number of log entries to display
    """
    time: dt.datetime
    until: dt.datetime
    prio_max: int = 7
    metric: str = "cpu"
    log_limit: int = 2000


def parse_timestamp(s: str) -> dt.datetime:
    """Parse timestamp string into datetime object.
    
    Supports formats:
    - "%Y-%m-%d %H:%M:%S" (e.g., "2024-01-15 14:30:00")
    - "%Y-%m-%d %H:%M" (e.g., "2024-01-15 14:30")
    
    Args:
        s: Timestamp string to parse
        
    Returns:
        Parsed datetime object
        
    Raises:
        SystemExit: If timestamp format is invalid
    """
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise SystemExit(f"Invalid time format: {s}")


class JournalPane(Static):
    """Widget for displaying Linux journal entries.
    
    This pane shows journal entries filtered by priority level and time range.
    Entries are displayed with proper line wrapping and formatting.
    
    Attributes:
        prio_max: Reactive maximum priority level for filtering
    """
    prio_max = reactive(7)

    def __init__(self, cfg: AppConfig):
        """Initialize the journal pane.
        
        Args:
            cfg: Application configuration
        """
        super().__init__()
        self.cfg = cfg
        self._log = Log()

    def compose(self) -> ComposeResult:
        """Compose the journal pane layout.
        
        Yields:
            Static header with time range
            Log widget for journal entries
        """
        yield Static(f"Journal {self.cfg.time} → {self.cfg.until}")
        yield self._log

    def set_prio(self, p: int) -> None:
        """Set maximum priority level and reload data.
        
        Args:
            p: Priority level (0-7, clamped to valid range)
        """
        self.prio_max = max(0, min(7, p))
        self.reload()

    def reload(self) -> None:
        """Reload journal entries from journalctl.
        
        Fetches journal entries within the configured time range and priority level,
        processes them for display with proper line wrapping.
        """
        self._log.clear()
        cmd = [
            "journalctl", "--no-pager",
            "--since", self.cfg.time.strftime("%Y-%m-%d %H:%M:%S"),
            "--until", self.cfg.until.strftime("%Y-%m-%d %H:%M:%S"),
            "-o", "json",
        ]
        if self.prio_max < 7:
            cmd += ["-p", f"0..{self.prio_max}"]

        try:
            out = subprocess.check_output(cmd, text=True)
        except Exception as e:
            self._log.write(f"Error: {e}")
            return

        count = 0
        for line in out.splitlines():
            if count >= self.cfg.log_limit:
                break
            try:
                rec = json.loads(line)
                msg = rec.get("MESSAGE", "")
                timestamp = rec.get("__REALTIME_TIMESTAMP", "")
                priority = rec.get("PRIORITY", "6")
                
                # Format timestamp if available
                if timestamp:
                    try:
                        # Convert microsecond timestamp to datetime
                        ts = dt.datetime.fromtimestamp(int(timestamp) / 1000000)
                        ts_str = ts.strftime("%H:%M:%S")
                    except (ValueError, TypeError):
                        ts_str = ""
                else:
                    ts_str = ""
                
                # Get priority info
                try:
                    prio_num = int(priority)
                    prio_name = PRIO_NAMES.get(prio_num, "UNK")
                except (ValueError, TypeError):
                    prio_num = 6
                    prio_name = "UNK"
                
                # Format the log line with timestamp and priority
                prefix = f"[{ts_str}] [{prio_name}] " if ts_str else f"[{prio_name}] "
                
                # Handle multi-line messages properly
                if msg:
                    for line_num, chunk in enumerate(msg.splitlines()):
                        if count >= self.cfg.log_limit:
                            break
                        # Add prefix only to first line of multi-line messages
                        if line_num == 0:
                            formatted_line = f"{prefix}{chunk}\n"
                        else:
                            formatted_line = f"{' ' * len(prefix)}{chunk}\n"
                        
                        self._log.write(formatted_line)
                        count += 1
                else:
                    # Empty message
                    self._log.write(f"{prefix}(empty message)\n")
                    count += 1
                    
            except json.JSONDecodeError:
                # Fallback for non-JSON lines
                self._log.write(line)
                count += 1


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


def build_args() -> AppConfig:
    """Parse command line arguments and build application configuration.
    
    Returns:
        AppConfig object with parsed arguments
        
    Raises:
        SystemExit: If arguments are invalid
    """
    ap = argparse.ArgumentParser(
        description="Journal+SAR TUI - Monitor system journal and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --time "2024-01-15 14:00" 
  %(prog)s --time "2024-01-15 14:00:00" 
        """
    )
    ap.add_argument("--time", required=True, 
                   help="Start time (YYYY-MM-DD HH:MM[:SS])")
    
    args = ap.parse_args()
    time = parse_timestamp(args.time)
    until = parse_timestamp(args.time) + timedelta(minutes=10)

    return AppConfig(time=time, until=until)


if __name__ == "__main__":
    cfg = build_args()
    app = JournalSarApp(cfg)
    app.run()
