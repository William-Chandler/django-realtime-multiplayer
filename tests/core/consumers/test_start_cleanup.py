import pytest
from unittest.mock import patch, AsyncMock

from core import consumers

@pytest.mark.asyncio
async def test_start_cleanup_runs_once():
    consumers.cleanup_started = False

    with patch("core.consumers.room_cleanup_loop", new=AsyncMock()) as mock_loop, \
         patch("core.consumers.asyncio.create_task") as mock_create:

        await consumers.start_cleanup()

        mock_create.assert_called_once()
        assert consumers.cleanup_started is True

@pytest.mark.asyncio
async def test_start_cleanup_does_not_run_twice():
    consumers.cleanup_started = True

    with patch("core.consumers.asyncio.create_task") as mock_create:
        await consumers.start_cleanup()
        mock_create.assert_not_called()

