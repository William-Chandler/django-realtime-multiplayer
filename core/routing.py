from django.urls import path
from .consumers import GameConsumer
from .global_consumer import GlobalConsumer

websocket_urlpatterns = [
    path("ws/game/<room_id>/", GameConsumer.as_asgi()),
    path("ws/game/global/", GlobalConsumer.as_asgi()),
]
