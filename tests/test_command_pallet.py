import datetime as dt
import pytest
from sar_journal.ui import JournalSarApp, HelpCommandProvider
from sar_journal.config import AppConfig


@pytest.fixture
def cfg():
    now = dt.datetime.now()
    return AppConfig(time=now, until=now + dt.timedelta(minutes=10))


@pytest.mark.asyncio
async def test_command_palette_has_show_help(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        # Check if the help command provider is registered
        help_provider = None
        for provider_class in app.COMMAND_PROVIDERS:
            if provider_class.__name__ == "HelpCommandProvider":
                help_provider = provider_class(app)
                break

        assert (
            help_provider is not None
        ), "HelpCommandProvider not found in COMMAND_PROVIDERS"

        # Test the provider can return our help command
        commands = []
        async for command in help_provider.search("Show helpful"):
            commands.append(command)

        assert len(commands) > 0, "Help command not found when searching 'Show helpful'"
        help_command = commands[0]
        assert "Show helpful information about sar_journal" in help_command.title


@pytest.mark.asyncio
async def test_show_help_opens_help_screen(cfg):
    app = JournalSarApp(cfg)

    async with app.run_test() as pilot:
        # Open the command palette (^P)
        await pilot.press("ctrl+p")

        # Type the command name using individual key presses
        for char in "Show helpful":
            if char == " ":
                await pilot.press("space")
            else:
                await pilot.press(char.lower())

        # Wait a moment for the command to be filtered
        await pilot.pause()

        # Confirm selection
        await pilot.press("enter")

        # Wait for the screen to be pushed
        await pilot.pause()

        # Now the HelpScreen should be on the stack
        assert any("HelpScreen" in type(s).__name__ for s in app.screen_stack)
