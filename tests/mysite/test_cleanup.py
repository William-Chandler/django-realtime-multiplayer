import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from mysite.cleanup import room_cleanup_loop


@pytest.mark.asyncio
async def test_room_cleanup_deletes_inactive_rooms(monkeypatch):
    # Fake Redis client
    fake_redis = AsyncMock()

    # Simulate one inactive room
    fake_redis.smembers.return_value = ["room123"]
    fake_redis.get.side_effect = [
        "0",        # connections = 0
        "1000",     # last_empty timestamp
    ]

    # Force loop to exit after first iteration
    async def fake_sleep(_):
        raise StopAsyncIteration()

    monkeypatch.setattr("mysite.cleanup.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    with patch("mysite.cleanup.delete_room", new_callable=AsyncMock) as mock_delete:
        # Run one iteration
        try:
            await room_cleanup_loop()
        except StopAsyncIteration:
            pass

        mock_delete.assert_called_once_with("room123")

        # Redis cleanup calls
        fake_redis.delete.assert_called_once_with(
            "room:room123:connections",
            "room:room123:last_empty",
        )
        fake_redis.srem.assert_called_once_with("rooms:active", "room123")


@pytest.mark.asyncio
async def test_room_cleanup_skips_active_rooms(monkeypatch):
    fake_redis = AsyncMock()

    fake_redis.smembers.return_value = ["roomABC"]
    fake_redis.get.side_effect = [
        "5",        # connections > 0 → skip
    ]

    async def fake_sleep(_):
        raise StopAsyncIteration()

    monkeypatch.setattr("mysite.cleanup.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    with patch("mysite.cleanup.delete_room", new_callable=AsyncMock) as mock_delete:
        try:
            await room_cleanup_loop()
        except StopAsyncIteration:
            pass

        mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_room_cleanup_skips_rooms_without_last_empty(monkeypatch):
    fake_redis = AsyncMock()

    fake_redis.smembers.return_value = ["roomXYZ"]
    fake_redis.get.side_effect = [
        "0",        # connections = 0
        None,       # last_empty missing → skip
    ]

    async def fake_sleep(_):
        raise StopAsyncIteration()

    monkeypatch.setattr("mysite.cleanup.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    with patch("mysite.cleanup.delete_room", new_callable=AsyncMock) as mock_delete:
        try:
            await room_cleanup_loop()
        except StopAsyncIteration:
            pass

        mock_delete.assert_not_called()
