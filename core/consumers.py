import json
import uuid
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from mysite.redis import redis_client

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.id = str(uuid.uuid4())
        self.stream = "game:room:main"

        await self.accept()

        # Send snapshot of existing players
        positions = await redis_client.hgetall("positions")

        for player_id, pos in positions.items():
            if not pos or "," not in pos:
                continue

            x, y = pos.split(",")

            try:
                int_x = int(x)
                int_y = int(y)
            except ValueError:
                continue

            await self.send(text_data=json.dumps({
                "id": player_id,
                "x": int_x,
                "y": int_y,
            }))

        # Start background reader
        self.reader_task = asyncio.create_task(self.stream_reader())

    async def disconnect(self, close_code):
        await redis_client.hdel("positions", self.id)

        await redis_client.xadd(
            self.stream,
            {"id": self.id, "disconnect": "1"},
            maxlen=1000,
            approximate=True
        )

        self.reader_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "x" not in data or "y" not in data:
            return
        if data["x"] is None or data["y"] is None:
            return

        await redis_client.hset(
            "positions",
            self.id,
            f"{data['x']},{data['y']}"
        )

        await redis_client.xadd(
            self.stream,
            {"id": self.id, "x": data["x"], "y": data["y"]},
            maxlen=1000,
            approximate=True
        )

    async def stream_reader(self):
        last_id = "$"

        while True:
            entries = await redis_client.xread(
                streams={self.stream: last_id},
                count=10,
                block=0
            )

            if entries:
                _, messages = entries[0]
                for msg_id, fields in messages:
                    last_id = msg_id

                    if "disconnect" in fields:
                        await self.send(text_data=json.dumps({
                            "id": fields["id"],
                            "disconnect": True
                        }))
                        continue

                    await self.send(text_data=json.dumps({
                        "id": fields["id"],
                        "x": fields["x"],
                        "y": fields["y"],
                    }))
