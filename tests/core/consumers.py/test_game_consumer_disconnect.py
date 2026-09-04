import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.consumers import GameConsumer


@pytest.mark.asyncio
async def test_disconnect_cleans_up_and_cancels_reader():
    # Fake ASGI scope
    scope = {
        "url_route": {"kwargs": {"room_id": "room123"}},
        "user": MagicMock(),
    }

    consumer = GameConsumer()
    consumer.scope = scope
    consumer.room_id = "room123"
    consumer.id = "abc"
    consumer.stream = "game:room:room123"
    consumer.channel_name = "test-channel"

    # Fake reader task stored on the consumer instance
    fake_task = MagicMock()
    consumer.reader_task = fake_task

    # Fake channel layer
    consumer.channel_layer = MagicMock()
    consumer.channel_layer.group_discard = AsyncMock()

    # Fake Redis client
    fake_redis = AsyncMock()
    fake_redis.delete = AsyncMock()
    fake_redis.hdel = AsyncMock()
    fake_redis.xadd = AsyncMock()
    fake_redis.decr = AsyncMock(return_value=0)
    fake_redis.set = AsyncMock()

    with patch("core.consumers.redis_client", fake_redis), \
         patch("core.consumers.time.time", return_value=123456789):

        await consumer.disconnect(close_code=1000)

    # Redis cleanup
    fake_redis.delete.assert_any_await("player:abc:connected")
    fake_redis.hdel.assert_awaited_with("positions:room123", "abc")
    fake_redis.xadd.assert_awaited()
    fake_redis.decr.assert_awaited_with("room:room123:connections")
    fake_redis.set.assert_awaited_with("room:room123:last_empty", 123456789)

    # Channels cleanup
    consumer.channel_layer.group_discard.assert_awaited_with(
        "room_room123",
        "test-channel",
    )

    # Reader cancellation (new logic: cancel only if consumer.reader_task exists)
    fake_task.cancel.assert_called_once()

    # Redis reader lock cleared
    fake_redis.delete.assert_any_await("room:room123:reader_running")
