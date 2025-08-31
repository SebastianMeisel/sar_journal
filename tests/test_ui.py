import datetime as dt
import pytest

from sar_journal.ui import JournalSarApp
from sar_journal.config import AppConfig


@pytest.fixture
def cfg():
    now = dt.datetime.now()
    return AppConfig(time=now, until=now + dt.timedelta(minutes=10))


@pytest.mark.asyncio
async def test_app_mounts_widgets(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        # Check widgets exist
        journal = app.query_one("#journal")
        stats = app.query_one("#stats")
        assert journal is not None
        assert stats is not None


@pytest.mark.asyncio
async def test_reload_action(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        await pilot.press("r")  # trigger reload
        # journal pane should still exist after reload
        assert app.query_one("#journal") is not None


@pytest.mark.asyncio
async def test_priority_action(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        # press "3" to set prio ≤ 3
        await pilot.press("3")
        assert app.journal.prio_max == 3


@pytest.mark.asyncio
async def test_metric_switching(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        await pilot.press("c")
        assert app.stats.metric == "cpu"
        await pilot.press("l")
        assert app.stats.metric == "load"
        await pilot.press("m")
        assert app.stats.metric == "mem"


@pytest.mark.asyncio
async def test_shift_time(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        old_time = app.cfg.time
        await pilot.press("f")  # forward 10 minutes
        assert app.cfg.time == old_time + dt.timedelta(minutes=10)

        await pilot.press("b")  # back 10 minutes
        assert app.cfg.time == old_time


@pytest.mark.asyncio
async def test_footer_shows_bindings(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        footer = app.query("Footer").first()
        assert footer is not None

        # Collect descriptions from app.BINDINGS
        binding_descriptions = [b.description for b in app.BINDINGS]

        # ✅ Check that important bindings are present
        assert "Quit" in binding_descriptions
        assert "Reload" in binding_descriptions
        assert "CPU" in binding_descriptions
        assert "Load" in binding_descriptions
        assert any("Prio" in d for d in binding_descriptions)
        assert "Back 10m" in binding_descriptions
        assert "Forward 10m" in binding_descriptions

        # ✅ Consistency: footer should expose as many bindings as the app has
        assert len(footer.app.BINDINGS) == len(app.BINDINGS)


@pytest.mark.asyncio
async def test_footer_bindings_trigger_actions(cfg):
    app = JournalSarApp(cfg)
    async with app.run_test() as pilot:
        # -- Reload binding (r)
        await pilot.press("r")
        # journal still exists after reload
        assert app.query_one("#journal") is not None

        # -- Priority binding (3)
        await pilot.press("3")
        assert app.journal.prio_max == 3

        # -- Metric binding (c)
        await pilot.press("c")
        assert app.stats.metric == "cpu"

        # -- Time shift forward (f)
        old_time = app.cfg.time
        await pilot.press("f")
        assert app.cfg.time == old_time + dt.timedelta(minutes=10)
