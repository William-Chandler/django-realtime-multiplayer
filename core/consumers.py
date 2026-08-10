import json
import uuid
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from mysite.redis import redis_client

## This ensures the dev environment never crashes if Redis isn’t running.
async def safe_redis(coro, fallback=None):
    try:
        return await coro
    except Exception:
        return fallback

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.id = str(uuid.uuid4())
        self.stream = "game:room:main"

        await self.accept()
        
        # Send full stroke history
        raw_strokes = await safe_redis(redis_client.lrange("strokes", 0, -1), [])
        strokes = [json.loads(s) for s in raw_strokes]

        # Send snapshot of existing players
        positions = await safe_redis(redis_client.hgetall("positions"), {})
        
        await self.send(text_data=json.dumps({
            "strokes": strokes
        }))

        for player_id, pos in positions.items():
            if not pos or "," not in pos:
                continue

            parts = pos.split(",")

            if len(parts) == 3:
                x, y, colour = parts
            else:
                # fallback for old entries
                x, y = parts
                colour = "red"

            try:
                int_x = int(x)
                int_y = int(y)
            except ValueError:
                continue

            await self.send(text_data=json.dumps({
                "id": player_id,
                "x": int_x,
                "y": int_y,
                "colour": colour,
            }))

        # Start background reader
        self.reader_task = asyncio.create_task(self.stream_reader())

    async def disconnect(self, close_code):
        await safe_redis(redis_client.hdel("positions", self.id))

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
        # Handle drawing strokes
        # ==========================
        if "stroke" in data:
            stroke = data["stroke"]

            # Store persistent stroke
            await safe_redis(redis_client.rpush("strokes", json.dumps(stroke)))

            # Broadcast stroke to all clients
            await safe_redis(redis_client.xadd(
                self.stream,
                {
                    "stroke": json.dumps(stroke)
                },
                maxlen=1000,
                approximate=True
            ))
            return

        # ==========================
        # Handle movement
        # ==========================
        if "x" not in data or "y" not in data:
            return
        if data["x"] is None or data["y"] is None:
            return

        await safe_redis(redis_client.hset(
            "positions",
            self.id,
            f"{data['x']},{data['y']},{data.get('colour', 'red')}"
        ))

        await safe_redis(redis_client.xadd(
            self.stream,
            {
                "id": self.id,
                "x": data["x"],
                "y": data["y"],
                "colour": data.get("colour", "red")
            },
            maxlen=1000,
            approximate=True
        ))



    async def stream_reader(self):
        last_id = "$"

        while True:
            entries = await safe_redis(redis_client.xread(
                streams={self.stream: last_id},
                count=10,
                block=0),
                []
            )

            if entries:
                _, messages = entries[0]
                for msg_id, fields in messages:
                    last_id = msg_id

                    # Disconnect event
                    if "disconnect" in fields:
                        await self.send(text_data=json.dumps({
                            "id": fields["id"],
                            "disconnect": True
                        }))
                        continue

                    # ==========================
                    # Stroke event 
                    # ==========================
                    if "stroke" in fields:
                        await self.send(text_data=json.dumps({
                            "stroke": json.loads(fields["stroke"])
                        }))
                        continue

                    # Movement event
                    await self.send(text_data=json.dumps({
                        "id": fields["id"],
                        "x": fields["x"],
                        "y": fields["y"],
                        "colour": fields.get("colour", "red"),
                    }))
