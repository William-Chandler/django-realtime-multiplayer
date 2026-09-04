import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from core.consumers import GameConsumer


@pytest.mark.asyncio
async def test_connect_sets_identity_and_joins_group():
    scope = {
        "url_route": {"kwargs": {"room_id": "room123"}},
        "user": MagicMock(is_anonymous=True),   # force anonymous path
    }

    consumer = GameConsumer()
    consumer.scope = scope
    consumer.channel_layer = MagicMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.channel_layer.group_discard = AsyncMock()
    consumer.channel_layer.group_send = AsyncMock()
    consumer.channel_name = "test-channel"
    consumer.accept = AsyncMock()
    consumer.send = AsyncMock()

    fake_redis = AsyncMock()
    fake_redis.sadd = AsyncMock()
    fake_redis.incr = AsyncMock(return_value=1)
    fake_redis.hset = AsyncMock()
    fake_redis.lrange = AsyncMock(return_value=[])
    fake_redis.hgetall = AsyncMock(return_value={})
    fake_redis.setnx = AsyncMock(return_value=1)
    fake_redis.set = AsyncMock()
    fake_redis.get = AsyncMock(return_value="1")

    with patch("core.consumers.redis_client", fake_redis), \
         patch("core.consumers.start_cleanup", new=AsyncMock()), \
         patch("core.consumers.asyncio.create_task", return_value=MagicMock()), \
         patch("core.consumers.get_default_colour", return_value="blue"), \
         patch("core.consumers.get_default_diameter", return_value=10), \
         patch("core.consumers.database_sync_to_async", lambda fn: AsyncMock(return_value=None)):

        await consumer.connect()

    assert consumer.room_id == "room123"
    assert consumer.stream == "game:room:room123"

    consumer.channel_layer.group_add.assert_awaited_with(
        "room_room123",
        "test-channel",
    )
    consumer.accept.assert_awaited()

    fake_redis.sadd.assert_awaited_with("rooms:active", "room123")
    fake_redis.incr.assert_awaited_with("room:room123:connections")
    fake_redis.hset.assert_awaited()
