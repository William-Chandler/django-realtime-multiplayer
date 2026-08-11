import json
import uuid
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from mysite.redis import redis_client
from django.conf import settings

def get_default_colour():
    return settings.DEFAULT_COLOUR


async def safe_redis(coro, fallback=None):
    try:
        return await coro
    except Exception:
        return fallback


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.stream = f"game:room:{self.room_id}"
        self.id = str(uuid.uuid4())

        await self.accept()

        # ==========================
        # Send full stroke history
        # ==========================
        raw_strokes = await safe_redis(
            redis_client.lrange(f"strokes:{self.room_id}", 0, -1),
            []
        )
        strokes = [json.loads(s) for s in raw_strokes]

        await self.send(text_data=json.dumps({
            "strokes": strokes
        }))

        # ==========================
        # Send snapshot of existing players
        # ==========================
        positions = await safe_redis(
            redis_client.hgetall(f"positions:{self.room_id}"),
            {}
        )

        for pid, pos in positions.items():
            try:
                x, y, colour = pos.split(",")
                await self.send(text_data=json.dumps({
                    "id": pid,
                    "x": int(x),
                    "y": int(y),
                    "colour": colour
                }))
            except Exception:
                continue

        # ==========================
        # Start Redis stream reader
        # ==========================
        self.reader_task = asyncio.create_task(self.stream_reader())


    async def disconnect(self, close_code):
        await safe_redis(redis_client.hdel(
            f"positions:{self.room_id}",
            self.id
        ))

        await safe_redis(redis_client.xadd(
            self.stream,
            {"id": self.id, "disconnect": "1"},
            maxlen=1000,
            approximate=True
        ))

        self.reader_task.cancel()


    async def receive(self, text_data):
        data = json.loads(text_data)

        # ==========================
        # 1. Stroke (drawing or click-dot)
        # ==========================
        if "stroke" in data or data.get("draw"):
            if "stroke" in data:
                stroke = data["stroke"]
            else:
                # Convert click into a dot stroke
                stroke = {
                    "x1": data["x"],
                    "y1": data["y"],
                    "x2": data["x"],
                    "y2": data["y"],
                    "colour": data.get("colour", get_default_colour()),
                    "diameter": data.get("diameter", 10)
                }

            # Store persistent stroke
            await safe_redis(redis_client.rpush(
                f"strokes:{self.room_id}",
                json.dumps(stroke)
            ))

            # Broadcast stroke
            await safe_redis(redis_client.xadd(
                self.stream,
                {"stroke": json.dumps(stroke)},
                maxlen=1000,
                approximate=True
            ))
            return

        # ==========================
        # 2. Movement
        # ==========================
        if "x" in data and "y" in data:
            await safe_redis(redis_client.hset(
                f"positions:{self.room_id}",
                self.id,
                f"{data['x']},{data['y']},{data.get('colour',get_default_colour())}"
            ))

            await safe_redis(redis_client.xadd(
                self.stream,
                {
                    "id": self.id,
                    "x": data["x"],
                    "y": data["y"],
                    "colour": data.get("colour", get_default_colour())
                },
                maxlen=1000,
                approximate=True
            ))


    async def stream_reader(self):
        last_id = "$"

        while True:
            entries = await safe_redis(
                redis_client.xread(
                    streams={self.stream: last_id},
                    count=10,
                    block=0
                ),
                []
            )

            if not entries:
                continue

            _, messages = entries[0]

            for msg_id, fields in messages:
                last_id = msg_id

                # Disconnect
                if "disconnect" in fields:
                    await self.send(text_data=json.dumps({
                        "id": fields["id"],
                        "disconnect": True
                    }))
                    continue

                # Stroke
                if "stroke" in fields:
                    await self.send(text_data=json.dumps({
                        "stroke": json.loads(fields["stroke"])
                    }))
                    continue

                # Movement
                await self.send(text_data=json.dumps({
                    "id": fields["id"],
                    "x": fields["x"],
                    "y": fields["y"],
                    "colour": fields.get("colour", get_default_colour())
                }))
