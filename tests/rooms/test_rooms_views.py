import json
from unittest.mock import patch, MagicMock, AsyncMock

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from rooms.models import Room
from whiteboards.models import SavedBoard

User = get_user_model()


class RoomViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        self.client.login(username="testuser", password="password123")

        self.room = Room.objects.create(room_id="t11", owner=self.user)
        self.room.set_password("secret")
        self.room.save()

    # ---------- create_room ----------

    def test_create_room_get(self):
        url = reverse("create_room")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rooms/create_room.html")

    def test_create_room_post_success(self):
        url = reverse("create_room")
        response = self.client.post(url, {"room_id": "newroom", "password": "pw"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(room_id="newroom").exists())

    def test_create_room_post_duplicate(self):
        url = reverse("create_room")
        response = self.client.post(url, {"room_id": "t11", "password": "pw"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", response.content.decode())

    # ---------- join_room ----------

    def test_join_room_get(self):
        url = reverse("join_room")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rooms/join_room.html")

    def test_join_room_post_success(self):
        url = reverse("join_room")
        response = self.client.post(url, {"room_id": "t11", "password": "secret"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/rooms/t11/", response["Location"])

    def test_join_room_wrong_password(self):
        url = reverse("join_room")
        response = self.client.post(url, {"room_id": "t11", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Incorrect password", response.content.decode())

    def test_join_room_not_found(self):
        url = reverse("join_room")
        response = self.client.post(url, {"room_id": "missing", "password": "pw"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Room not found", response.content.decode())

    # ---------- room_page ----------

    def test_room_page(self):
        url = reverse("room_page", args=["t11"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rooms/room.html")
        self.assertEqual(response.context["room"].room_id, "t11")

    # ---------- load_room_state ----------

    @patch("rooms.views.load_state_from_s3")
    @patch("rooms.views.set_room_strokes")
    def test_load_room_state_success(self, mock_set, mock_load):
        mock_load.return_value = [{"x": 1}]
        url = reverse("load_room_state", args=["t11"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["strokes"], [{"x": 1}])
        mock_set.assert_called_once()

    def test_load_room_state_not_owner(self):
        other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="password123",
        )
        self.client.login(username="other", password="password123")

        url = reverse("load_room_state", args=["t11"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    @patch("rooms.views.load_state_from_s3")
    def test_load_room_state_empty(self, mock_load):
        mock_load.return_value = None
        url = reverse("load_room_state", args=["t11"])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "empty")

    # ---------- load_user_board_into_room ----------

    @patch("rooms.views.load_board_from_s3")
    @patch("rooms.views.get_channel_layer")
    @patch("rooms.views.set_room_strokes", new_callable=AsyncMock)
    def test_load_user_board_into_room_success(
        self, mock_set, mock_get_channel_layer, mock_load
    ):
        board = SavedBoard.objects.create(
            owner=self.user,
            name="Test Board",
            s3_key="users/1/boards/abc.json",
        )

        mock_load.return_value = [{"x": 1}]

        # Fix: async group_send
        mock_layer = MagicMock()
        mock_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer

        url = f"/rooms/t11/load_board/{board.id}/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["loaded_strokes"], 1)
        self.assertEqual(data["board_name"], "Test Board")

        mock_set.assert_called_once()
        mock_layer.group_send.assert_called_once()


    @patch("rooms.views.load_board_from_s3")
    def test_load_user_board_missing_file(self, mock_load):
        board = SavedBoard.objects.create(
            owner=self.user,
            name="Test Board",
            s3_key="users/1/boards/abc.json",
        )
        mock_load.return_value = None

        url = f"/rooms/t11/load_board/{board.id}/"
        response = self.client.post(url)
        data = json.loads(response.content)

        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "Board file missing")

    def test_load_user_board_not_owner(self):
        other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="password123",
        )
        self.client.login(username="other", password="password123")

        board = SavedBoard.objects.create(
            owner=self.user,
            name="Test Board",
            s3_key="users/1/boards/abc.json",
        )

        url = f"/rooms/t11/load_board/{board.id}/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
