import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from core.consumers import GameConsumer


@pytest.mark.asyncio
async def test_receive_movement_updates_position_and_stream():
    # Fake ASGI scope
    scope = {
        "url_route": {"kwargs": {"room_id": "room123"}},
        "user": MagicMock(),
    }

    consumer = GameConsumer()
    consumer.scope = scope
    consumer.room_id = "room123"
    consumer.stream = "game:room:room123"
    consumer.id = "abc"

    # Server-side enforced identity
    consumer.colour = "red"
    consumer.diameter = 5

    # Fake Redis
    fake_redis = AsyncMock()
    fake_redis.hset = AsyncMock()
    fake_redis.xadd = AsyncMock()

    with patch("core.consumers.redis_client", fake_redis):
        await consumer.receive(text_data=json.dumps({
            "x": 10,
            "y": 20
        }))

    # Position stored in Redis hash
    fake_redis.hset.assert_awaited_with(
        "positions:room123",
        "abc",
        "10,20,red"
    )

    # Movement broadcast via Redis stream
    fake_redis.xadd.assert_awaited_with(
        "game:room:room123",
        {
            "id": "abc",
            "x": 10,
            "y": 20,
            "colour": "red"
        },
        maxlen=1000,
        approximate=True
    )
