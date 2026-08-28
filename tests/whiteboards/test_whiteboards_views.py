import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from whiteboards.models import SavedBoard

User = get_user_model()


class WhiteboardViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pw12345"
        )
        self.client.login(username="testuser", password="pw12345")

    # ============================
    # my_boards
    # ============================

    def test_my_boards_empty(self):
        url = reverse("my_boards")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_my_boards_returns_boards(self):
        b1 = SavedBoard.objects.create(
            owner=self.user,
            name="Board A",
            s3_key="users/1/boards/a.json"
        )
        b2 = SavedBoard.objects.create(
            owner=self.user,
            name="Board B",
            s3_key="users/1/boards/b.json"
        )

        url = reverse("my_boards")
        response = self.client.get(url)
        data = json.loads(response.content)

        # Should be ordered newest first
        self.assertEqual(data[0]["id"], b2.id)
        self.assertEqual(data[1]["id"], b1.id)

    # ============================
    # save_whiteboard
    # ============================

    def test_save_whiteboard_requires_post(self):
        url = reverse("save_whiteboard", args=["room1"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(json.loads(response.content)["error"], "POST required")

    def test_save_whiteboard_missing_name(self):
        url = reverse("save_whiteboard", args=["room1"])
        response = self.client.post(
            url,
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)["error"], "Missing board name")

    @patch("whiteboards.views.get_room_strokes")
    @patch("whiteboards.views.save_board_to_s3")
    def test_save_whiteboard_new_board(self, mock_save_s3, mock_get_strokes):
        mock_get_strokes.return_value = [{"x": 1}]

        url = reverse("save_whiteboard", args=["room1"])
        response = self.client.post(
            url,
            data=json.dumps({"name": "My Board"}),
            content_type="application/json"
        )

        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["created"])

        board = SavedBoard.objects.get(id=data["id"])
        self.assertEqual(board.name, "My Board")
        self.assertEqual(board.s3_key, f"users/{self.user.id}/boards/My_Board.json")

        mock_save_s3.assert_called_once()

    @patch("whiteboards.views.get_room_strokes")
    @patch("whiteboards.views.save_board_to_s3")
    def test_save_whiteboard_existing_no_overwrite(self, mock_save_s3, mock_get_strokes):
        SavedBoard.objects.create(
            owner=self.user,
            name="My Board",
            s3_key="users/1/boards/old.json"
        )

        url = reverse("save_whiteboard", args=["room1"])
        response = self.client.post(
            url,
            data=json.dumps({"name": "My Board"}),
            content_type="application/json"
        )

        data = json.loads(response.content)
        self.assertEqual(data, {"exists": True})
        mock_save_s3.assert_not_called()

    @patch("whiteboards.views.get_room_strokes")
    @patch("whiteboards.views.save_board_to_s3")
    def test_save_whiteboard_overwrite(self, mock_save_s3, mock_get_strokes):
        mock_get_strokes.return_value = [{"x": 1}]

        board = SavedBoard.objects.create(
            owner=self.user,
            name="My Board",
            s3_key="users/1/boards/old.json"
        )

        url = reverse("save_whiteboard", args=["room1"])
        response = self.client.post(
            url,
            data=json.dumps({"name": "My Board", "overwrite": True}),
            content_type="application/json"
        )

        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["overwritten"])
        self.assertEqual(data["id"], board.id)

        board.refresh_from_db()
        self.assertEqual(board.s3_key, f"users/{self.user.id}/boards/My_Board.json")

        mock_save_s3.assert_called_once()
