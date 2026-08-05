import json
from channels.generic.websocket import AsyncWebsocketConsumer
import uuid

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.id = str(uuid.uuid4())
        await self.channel_layer.group_add("game", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("game", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        data["id"] = self.id

        await self.channel_layer.group_send(
            "game",
            {
                "type": "game_message",
                "data": data,
            }
        )

    async def game_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))
