import pytest
from django.contrib.auth import get_user_model
from rooms.models import Room


def test_set_password_hashes_password():
    room = Room(room_id="abc123")
    room.set_password("secret123")

    assert room.password_hash != "secret123"
    assert room.password_hash.startswith("pbkdf2_")  # Django default


def test_check_password_correct():
    room = Room(room_id="abc123")
    room.set_password("mypassword")

    assert room.check_password("mypassword") is True


def test_check_password_incorrect():
    room = Room(room_id="abc123")
    room.set_password("mypassword")

    assert room.check_password("wrong") is False


def test_owner_can_be_null(db):
    room = Room.objects.create(room_id="abc123", password_hash="x", owner=None)
    assert room.owner is None


def test_room_id_must_be_unique(db):
    Room.objects.create(room_id="unique123", password_hash="x")

    with pytest.raises(Exception):
        Room.objects.create(room_id="unique123", password_hash="y")
