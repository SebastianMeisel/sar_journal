from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import rich.repr
from textual.app import ComposeResult
from textual.widgets import Footer
from textual.widgets._footer import FooterKey

if TYPE_CHECKING:
    from textual.screen import Screen


@rich.repr.auto
class JournalFooter(Footer):
    # ALLOW_SELECT = False
    DEFAULT_CSS = """
    JournalFooter {
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        if not self._bindings_ready:
            return
        self.styles.grid_size_columns = 15

        #Hardcoded Journal bindings for testing
        yield FooterKey("1", "1", "alert", "prio(1)", tooltip="show only alerts")
        yield FooterKey("2", "2", "critical", "prio(2)", tooltip="show only criticals or above")
        yield FooterKey("3", "3", "error", "prio(3)", tooltip="show only errors or above")
        yield FooterKey("4", "4", "warning", "prio(4)", tooltip="show only warnings or above")
        yield FooterKey("5", "5", "notice", "prio(5)", tooltip="show only notices or above")
        yield FooterKey("6", "6", "info", "prio(6)", tooltip="show only infos or above")
        yield FooterKey("7", "7", "debug", "prio(7)", tooltip="show only debugs or above")

        # Hardcoded General bindings for testing
        yield FooterKey("q", "q", "Quit", "quit", tooltip="quit the application")
        yield FooterKey("r", "r", "Reload", "reload", tooltip="reload the application")
        yield FooterKey("b", "b", "Back 10m", "shift_time(-10)", tooltip="shift time window back 10 minutes")
        yield FooterKey("f", "f", "Forward 10m", "shift_time(10)", tooltip="shift time window forward 10 minutes")
        

@rich.repr.auto
class SarFooter(Footer):
    # ALLOW_SELECT = False
    DEFAULT_CSS = """
    SarFooter {
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        if not self._bindings_ready:
            return
        self.styles.grid_size_columns = 15
        # Hardcoded SAR bindings
        yield FooterKey("l", "l", "Load", "metric(load)", tooltip="show load statistics")
        yield FooterKey("m", "m", "Mem", "metric(mem)", tooltip="show memory statistics")
        yield FooterKey("d", "d", "Disk", "metric(disk)", tooltip="show disk statistics")
        yield FooterKey("n", "n", "Network", "metric(net)", tooltip="show network statistics")
        yield FooterKey("E", "E", "Network error", "metric(edev)", tooltip="show network device errors")
        yield FooterKey("T", "T", "TCP error", "metric(etcp)", tooltip="show tcp errors")