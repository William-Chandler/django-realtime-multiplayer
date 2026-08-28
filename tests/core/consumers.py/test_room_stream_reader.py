import pytest
from unittest.mock import AsyncMock, patch

from core.consumers import room_stream_reader


class StopReader(BaseException):
    pass


@pytest.mark.asyncio
async def test_room_stream_reader_sends_messages():
    room_id = "room123"

    async def fake_xread(*args, **kwargs):
        fake_xread.calls += 1

        if fake_xread.calls == 1:
            return [
                (
                    f"game:room:{room_id}",
                    [
                        ("1-0", {"foo": "bar"}),
                        ("1-1", {"baz": "qux"}),
                    ],
                )
            ]
        raise StopReader()

    fake_xread.calls = 0

    fake_channel_layer = AsyncMock()
    fake_channel_layer.group_send = AsyncMock()

    with patch("core.consumers.redis_client.xread", side_effect=fake_xread), \
        patch("core.consumers.get_channel_layer", return_value=fake_channel_layer), \
        patch("core.consumers.asyncio.sleep", new=AsyncMock()):

        with pytest.raises(StopReader):
            await room_stream_reader(room_id)

    fake_channel_layer.group_send.assert_any_await(
        "room_room123",
        {"type": "room.event", "fields": {"foo": "bar"}},
    )

    fake_channel_layer.group_send.assert_any_await(
        "room_room123",
        {"type": "room.event", "fields": {"baz": "qux"}},
    )

    assert fake_channel_layer.group_send.await_count == 2
