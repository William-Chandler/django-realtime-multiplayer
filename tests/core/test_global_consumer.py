import uuid
import pytest
from unittest.mock import AsyncMock, patch

from core.global_consumer import GlobalConsumer
from core.consumers import GameConsumer


@pytest.mark.asyncio
async def test_global_consumer_sets_room_id_and_stream():
    consumer = GlobalConsumer()

    # Fake scope so GameConsumer doesn't explode
    consumer.scope = {"url_route": {"kwargs": {}}}

    with patch.object(GameConsumer, "connect", new_callable=AsyncMock) as mock_super:
        await consumer.connect()

    assert consumer.room_id == "global"
    assert consumer.stream == "game:room:global"


@pytest.mark.asyncio
async def test_global_consumer_sets_uuid_id():
    consumer = GlobalConsumer()
    consumer.scope = {"url_route": {"kwargs": {}}}

    with patch.object(GameConsumer, "connect", new_callable=AsyncMock):
        await consumer.connect()

    # UUID should be valid
    uuid_obj = uuid.UUID(consumer.id)
    assert str(uuid_obj) == consumer.id


@pytest.mark.asyncio
async def test_global_consumer_calls_super_connect():
    consumer = GlobalConsumer()
    consumer.scope = {"url_route": {"kwargs": {}}}

    with patch.object(GameConsumer, "connect", new_callable=AsyncMock) as mock_super:
        await consumer.connect()

    mock_super.assert_awaited_once()
