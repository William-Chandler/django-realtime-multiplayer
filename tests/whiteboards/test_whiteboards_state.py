import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from whiteboards.state import (
    get_room_strokes,
    set_room_strokes,
    s3_key_for_room_state,
    s3_key_for_user_board,
    save_board_to_s3,
    save_state_to_s3,
    load_state_from_s3,
    load_board_from_s3,
    delete_room_state_from_s3,
)


# ============================
# Redis tests (async)
# ============================

@pytest.mark.asyncio
async def test_get_room_strokes():
    fake_redis = MagicMock()
    fake_redis.lrange = AsyncMock(return_value=[
        json.dumps({"x": 1}),
        json.dumps({"x": 2})
    ])

    with patch("whiteboards.state.get_redis_client", return_value=fake_redis):
        strokes = await get_room_strokes("room1")

    assert strokes == [{"x": 1}, {"x": 2}]
    fake_redis.lrange.assert_called_once_with("strokes:room1", 0, -1)


@pytest.mark.asyncio
async def test_set_room_strokes():
    fake_redis = MagicMock()
    fake_redis.delete = AsyncMock()
    fake_redis.rpush = AsyncMock()

    strokes = [{"a": 1}, {"b": 2}]

    with patch("whiteboards.state.get_redis_client", return_value=fake_redis):
        await set_room_strokes("room1", strokes)

    fake_redis.delete.assert_called_once_with("strokes:room1")
    assert fake_redis.rpush.call_count == 2
    fake_redis.rpush.assert_any_call("strokes:room1", json.dumps({"a": 1}))
    fake_redis.rpush.assert_any_call("strokes:room1", json.dumps({"b": 2}))


# ============================
# Key helpers
# ============================

def test_s3_key_for_room_state():
    assert s3_key_for_room_state("abc") == "rooms/abc/state.json"


def test_s3_key_for_user_board():
    assert s3_key_for_user_board(42, "xyz") == "users/42/boards/xyz.json"


# ============================
# S3 save/load tests
# ============================

def test_save_board_to_s3():
    fake_storage = MagicMock()

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        save_board_to_s3("users/1/boards/a.json", [{"x": 1}])

    args, kwargs = fake_storage.save.call_args
    assert args[0] == "users/1/boards/a.json"

    content_file = args[1]
    payload = content_file.read().decode()
    assert json.loads(payload) == {"strokes": [{"x": 1}]}


def test_save_state_to_s3():
    fake_storage = MagicMock()

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        save_state_to_s3("room1", [{"x": 1}])

    args, kwargs = fake_storage.save.call_args
    assert args[0] == "rooms/room1/state.json"


def test_load_state_from_s3_exists():
    fake_storage = MagicMock()
    fake_storage.exists.return_value = True
    fake_storage.open.return_value.__enter__.return_value.read.return_value = (
        b'{"strokes":[{"x":1},{"x":2}]}'
    )

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        strokes = load_state_from_s3("room1")

    assert strokes == [{"x": 1}, {"x": 2}]


def test_load_state_from_s3_missing():
    fake_storage = MagicMock()
    fake_storage.exists.return_value = False

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        assert load_state_from_s3("room1") is None


def test_load_board_from_s3_exists():
    fake_storage = MagicMock()
    fake_storage.exists.return_value = True
    fake_storage.open.return_value.__enter__.return_value.read.return_value = (
        b'{"strokes":[{"x":9}]}'
    )

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        strokes = load_board_from_s3("users/1/boards/a.json")

    assert strokes == [{"x": 9}]


def test_load_board_from_s3_missing():
    fake_storage = MagicMock()
    fake_storage.exists.return_value = False

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        assert load_board_from_s3("users/1/boards/a.json") is None


# ============================
# Delete tests
# ============================

def test_delete_room_state_from_s3_exists():
    fake_storage = MagicMock()
    fake_storage.exists.return_value = True

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        delete_room_state_from_s3("room1")

    fake_storage.delete.assert_called_once_with("rooms/room1/state.json")


def test_delete_room_state_from_s3_missing():
    fake_storage = MagicMock()
    fake_storage.exists.return_value = False

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        delete_room_state_from_s3("room1")

    fake_storage.delete.assert_not_called()


def test_delete_room_state_from_s3_silent_failure():
    fake_storage = MagicMock()
    fake_storage.exists.side_effect = Exception("boom")

    with patch("whiteboards.state.get_storage", return_value=fake_storage):
        delete_room_state_from_s3("room1")  # should not raise

    # No exception = success
