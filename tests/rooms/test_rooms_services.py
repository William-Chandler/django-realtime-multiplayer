import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from rooms.services import delete_room, purge_all_rooms, wait_for_services
from rooms.models import Room


@pytest.mark.asyncio
async def test_delete_room():
    fake_redis = AsyncMock()
    fake_redis.delete = AsyncMock()

    with patch("rooms.services.get_redis_client", return_value=fake_redis):
        with patch.object(Room.objects, "filter") as mock_filter:
            mock_filter.return_value.delete = MagicMock(return_value=None)

            with patch("rooms.services.delete_room_state_from_s3") as mock_s3:
                await delete_room("abc123")

                fake_redis.delete.assert_any_call("positions:abc123")
                fake_redis.delete.assert_any_call("strokes:abc123")
                fake_redis.delete.assert_any_call("game:room:abc123")

                mock_filter.return_value.delete.assert_called_once()
                mock_s3.assert_called_once_with("abc123")


@pytest.mark.asyncio
async def test_purge_all_rooms_no_rooms():
    with patch("rooms.services.wait_for_services", new=AsyncMock()):
        with patch.object(Room.objects, "values_list") as mock_values:
            mock_values.return_value = []

            await purge_all_rooms()


@pytest.mark.asyncio
async def test_purge_all_rooms_with_rooms():
    fake_redis = AsyncMock()
    fake_redis.delete = AsyncMock()

    with patch("rooms.services.wait_for_services", new=AsyncMock()):
        with patch("rooms.services.get_redis_client", return_value=fake_redis):
            with patch.object(Room.objects, "values_list") as mock_values:
                mock_values.return_value = ["r1", "r2"]

                with patch("rooms.services.delete_room_state_from_s3") as mock_s3:
                    with patch.object(Room.objects, "all") as mock_all:
                        mock_all.return_value.delete = MagicMock(return_value=None)

                        await purge_all_rooms()

                        fake_redis.delete.assert_called_once()
                        args = fake_redis.delete.call_args[0]
                        assert "positions:r1" in args
                        assert "strokes:r1" in args
                        assert "game:room:r1" in args
                        assert "positions:r2" in args
                        assert "strokes:r2" in args
                        assert "game:room:r2" in args

                        mock_s3.assert_any_call("r1")
                        mock_s3.assert_any_call("r2")


@pytest.mark.asyncio
async def test_wait_for_services():
    fake_redis = AsyncMock()
    fake_redis.ping = AsyncMock()

    fake_storage = MagicMock()
    fake_storage.exists = MagicMock()

    with patch("rooms.services.get_redis_client", return_value=fake_redis):
        with patch("whiteboards.state.get_storage", return_value=fake_storage):
            await wait_for_services()

            fake_redis.ping.assert_called()
            fake_storage.exists.assert_called_once_with("rooms/__startup_test__")
