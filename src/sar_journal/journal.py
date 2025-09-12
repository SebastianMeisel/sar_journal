import subprocess, json, datetime as dt
from textual.widgets import Static, Log
from textual.reactive import reactive
from textual.app import ComposeResult
from .config import AppConfig
from .constants import PRIO_NAMES

class JournalPane(Static):
    """Widget for displaying Linux journal entries.
    
    This pane shows journal entries filtered by priority level and time range.
    Entries are displayed with proper line wrapping and formatting.
    
    Attributes:
        prio_max: Reactive maximum priority level for filtering
    """
    prio_max = reactive(7)
    header_text = reactive("")

    def __init__(self, cfg: AppConfig):
        """Initialize the journal pane.
        
        Args:
            cfg: Application configuration
        """
        super().__init__()
        self.cfg = cfg
        self._log = Log()
        self._header_static = Static("")  # Initialize with empty string
        self.header_text = f"Journal {self.cfg.time} → {self.cfg.until}"

    def compose(self) -> ComposeResult:
        """Compose the journal pane layout.
        
        Yields:
            Static header with time range
            Log widget for journal entries
        """
        yield self._header_static
        yield self._log

    def set_prio(self, p: int) -> None:
        """Set maximum priority level and reload data.
        
        Args:
            p: Priority level (0-7, clamped to valid range)
        """
        self.prio_max = max(0, min(7, p))
        self.reload()

    def watch_header_text(self, new_text: str) -> None:
        """Update the header static widget when header_text changes."""
        self._header_static.update(new_text)

    def reload(self) -> None:
        """Reload journal entries from journalctl.
        
        Fetches journal entries within the configured time range and priority level,
        processes them for display with proper line wrapping.
        """
        self._log.clear()
        self.header_text = f"Journal {self.cfg.time} → {self.cfg.until}"
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
                if not isinstance(msg, str):
                    msg = str(msg)
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
