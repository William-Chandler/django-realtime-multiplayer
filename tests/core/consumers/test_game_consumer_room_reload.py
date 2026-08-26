import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from core.consumers import GameConsumer


def make_consumer():
    scope = {
        "url_route": {"kwargs": {"room_id": "room123"}},
        "user": MagicMock(),
    }

    c = GameConsumer()
    c.scope = scope
    c.room_id = "room123"
    c.channel_name = "test-channel"
    c.send = AsyncMock()
    return c


@pytest.mark.asyncio
async def test_room_reload_sends_full_reload_packet():
    consumer = make_consumer()

    event = {"strokes": [{"x1": 1}, {"x1": 2}]}

    await consumer.room_reload(event)

    consumer.send.assert_awaited_with(
        text_data=json.dumps({
            "reload": True,
            "strokes": [{"x1": 1}, {"x1": 2}]
        })
    )
