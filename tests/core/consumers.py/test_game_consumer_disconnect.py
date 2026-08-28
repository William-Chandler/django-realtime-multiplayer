import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.consumers import GameConsumer, ROOM_READERS


@pytest.mark.asyncio
async def test_disconnect_cleans_up_and_cancels_reader():
    # Fake ASGI scope
    scope = {
        "url_route": {"kwargs": {"room_id": "room123"}},
        "user": MagicMock(),
    }

    # Instantiate consumer correctly
    consumer = GameConsumer()
    consumer.scope = scope
    consumer.room_id = "room123"
    consumer.id = "abc"
    consumer.stream = "game:room:room123"

    # Fake channel layer
    consumer.channel_layer = MagicMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.channel_layer.group_discard = AsyncMock()
    consumer.channel_layer.group_send = AsyncMock()
    consumer.channel_name = "test-channel"

    # Fake Redis client
    fake_redis = AsyncMock()
    fake_redis.hdel = AsyncMock()
    fake_redis.xadd = AsyncMock()
    fake_redis.decr = AsyncMock(return_value=0)
    fake_redis.set = AsyncMock()

    # Fake reader task
    fake_task = MagicMock()
    ROOM_READERS["room123"] = fake_task

    with patch("core.consumers.redis_client", fake_redis), \
         patch("core.consumers.time.time", return_value=123456789):

        await consumer.disconnect(close_code=1000)

    # Redis cleanup
    fake_redis.hdel.assert_awaited_with("positions:room123", "abc")
    fake_redis.xadd.assert_awaited()  # disconnect broadcast
    fake_redis.decr.assert_awaited_with("room:room123:connections")
    fake_redis.set.assert_awaited_with("room:room123:last_empty", 123456789)

    # Channels cleanup
    consumer.channel_layer.group_discard.assert_awaited_with(
        "room_room123",
        "test-channel",
    )

    # Reader cancellation
    fake_task.cancel.assert_called_once()

    # Reader removed from registry
    assert "room123" not in ROOM_READERS
