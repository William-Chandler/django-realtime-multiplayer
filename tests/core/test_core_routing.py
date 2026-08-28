import pytest
from django.urls import URLPattern

from core.routing import websocket_urlpatterns


def test_websocket_urlpatterns_count():
    assert len(websocket_urlpatterns) == 2


def test_game_consumer_route():
    route = websocket_urlpatterns[0]

    assert isinstance(route, URLPattern)
    assert route.pattern._route == "ws/game/<room_id>/"


def test_global_consumer_route():
    route = websocket_urlpatterns[1]

    assert isinstance(route, URLPattern)
    assert route.pattern._route == "ws/game/global/"
