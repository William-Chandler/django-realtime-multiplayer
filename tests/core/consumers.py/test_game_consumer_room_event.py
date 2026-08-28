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
async def test_room_event_disconnect():
    consumer = make_consumer()

    event = {"fields": {"id": "abc", "disconnect": "1"}}
    await consumer.room_event(event)

    consumer.send.assert_awaited_with(
        text_data=json.dumps({
            "id": "abc",
            "disconnect": True
        })
    )


@pytest.mark.asyncio
async def test_room_event_stroke():
    consumer = make_consumer()

    event = {"fields": {"stroke": json.dumps({"x1": 1})}}
    await consumer.room_event(event)

    consumer.send.assert_awaited_with(
        text_data=json.dumps({
            "stroke": {"x1": 1}
        })
    )


@pytest.mark.asyncio
async def test_room_event_movement():
    consumer = make_consumer()

    event = {
        "fields": {
            "id": "abc",
            "x": 10,
            "y": 20,
            "colour": "blue"
        }
    }

    await consumer.room_event(event)

    consumer.send.assert_awaited_with(
        text_data=json.dumps({
            "id": "abc",
            "x": 10,
            "y": 20,
            "colour": "blue"
        })
    )
