import datetime as dt
import pytest
from sar_journal.ui import JournalSarApp
from sar_journal.config import AppConfig


@pytest.fixture
def cfg():
    now = dt.datetime.now()
    return AppConfig(time=now, until=now + dt.timedelta(minutes=10))


@pytest.mark.asyncio
async def test_command_palette_has_show_pallet(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        # Simulate opening the command palette (^p)
        await pilot.press("ctrl+p")

        # The top screen should be the Command Palette
        assert "CommandPalette" in type(app.screen_stack[-1]).__name__

        commands = list(app.get_system_commands(app.screen))

        ids = []
        for c in commands:
            if hasattr(c, "id"):          # Command in Textual 0.5+
                ids.append(c.id)
            elif hasattr(c, "name"):      # older Command API
                ids.append(c.name)

        assert "Show helpful information about sar_journal" in ids
