import json
import uuid
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from mysite.redis import redis_client

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.id = str(uuid.uuid4())
        self.stream = "game:room:main"
        self.last_id = "0-0"  # start at beginning or "$" for only new messages

        await self.accept()

        # Start background reader
        self.reader_task = asyncio.create_task(self.stream_reader())

    async def disconnect(self, close_code):
        self.reader_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        await redis_client.xadd(
            self.stream,
            {
                "id": self.id,
                "x": data["x"],
                "y": data["y"],
            }
        )

    async def game_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    async def stream_reader(self):
        try:
            while True:
                # Block until new messages arrive
                messages = await redis_client.xread(
                    {self.stream: self.last_id},
                    block=5000,  # 5 seconds
                    count=10
                )

                if not messages:
                    continue

                # messages = [(stream_name, [(id, fields), ...])]
                _, entries = messages[0]

                for entry_id, fields in entries:
                    self.last_id = entry_id
                    await self.send(text_data=json.dumps(fields))

        except asyncio.CancelledError:
            pass
