import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from core.consumers import GameConsumer


@pytest.mark.asyncio
async def test_receive_stroke_stores_and_broadcasts():
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
    fake_redis.rpush = AsyncMock()
    fake_redis.xadd = AsyncMock()

    with patch("core.consumers.redis_client", fake_redis):
        await consumer.receive(text_data=json.dumps({
            "stroke": {
                "x1": 1,
                "y1": 2,
                "x2": 3,
                "y2": 4
            }
        }))

    # Stroke stored in Redis list
    fake_redis.rpush.assert_awaited_with(
        "strokes:room123",
        json.dumps({
            "x1": 1,
            "y1": 2,
            "x2": 3,
            "y2": 4,
            "colour": "red",
            "diameter": 5
        })
    )

    # Stroke broadcast via Redis stream
    fake_redis.xadd.assert_awaited_with(
        "game:room:room123",
        {"stroke": json.dumps({
            "x1": 1,
            "y1": 2,
            "x2": 3,
            "y2": 4,
            "colour": "red",
            "diameter": 5
        })},
        maxlen=1000,
        approximate=True
    )
