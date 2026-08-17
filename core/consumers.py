import json
import uuid
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from mysite.redis import redis_client
from django.conf import settings
from whiteboards.state import load_state_from_s3


# ============================================================
# Per-room reader registry (per-process)
# ============================================================

ROOM_READERS = {}      # room_id → asyncio.Task
ROOM_CONNECTIONS = {}  # room_id → count of active connections


def get_default_colour():
    return settings.DEFAULT_COLOUR

def get_default_diameter():
    return getattr(settings, "DEFAULT_DIAMETER", 10)


async def safe_redis(coro, fallback=None):
    try:
        return await coro
    except Exception as e:
        # Log redis errors
        import logging
        logger = logging.getLogger("redis")
        logger.error(f"Redis error: {type(e).__name__}: {e}", exc_info=True)
        return fallback


# ============================================================
# Redis stream reader (one per room per worker)
# ============================================================

async def room_stream_reader(room_id):
    """
    Single reader per room per worker.
    Reads Redis stream and broadcasts via Channels group.
    """
    print("READER for room_id", room_id)
    channel_layer = get_channel_layer()
    stream = f"game:room:{room_id}"
    last_id = "$"

    while True:
        try:
            entries = await redis_client.xread(
                streams={stream: last_id},
                count=10,
                block=0
            )
        except Exception:
            continue

        if not entries:
            continue

        _, messages = entries[0]

        for msg_id, fields in messages:
            last_id = msg_id

            # Broadcast to group
            await channel_layer.group_send(
                f"room_{room_id}",
                {
                    "type": "room.event",
                    "fields": fields
                }
            )


# ============================================================
# WebSocket Consumer
# ============================================================

class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.id = str(uuid.uuid4())
        self.stream = f"game:room:{self.room_id}"

        # SERVER-SIDE identity (never trust browser)
        user = self.scope["user"]

        # Fetch profile safely in async context
        profile = await database_sync_to_async(lambda: getattr(user, "userprofile", None))()

        if profile:
            self.colour = await database_sync_to_async(lambda: getattr(profile, "colour_preference", get_default_colour()))()
            self.diameter = await database_sync_to_async(lambda: getattr(profile, "diameter_preference", get_default_diameter()))()
        else:
            self.colour = get_default_colour()
            self.diameter = get_default_diameter()



        # Join Channels group
        await self.channel_layer.group_add(
            f"room_{self.room_id}",
            self.channel_name
        )

        # Track active connections
        ROOM_CONNECTIONS[self.room_id] = ROOM_CONNECTIONS.get(self.room_id, 0) + 1

        # Start reader if needed
        if ROOM_CONNECTIONS[self.room_id] == 1:
            ROOM_READERS[self.room_id] = asyncio.create_task(
                room_stream_reader(self.room_id)
            )

        await self.accept()

        # Store initial position
        await safe_redis(redis_client.hset(
            f"positions:{self.room_id}",
            self.id,
            f"0,0,{self.colour}"
        ))

        # Broadcast initial cursor to existing users
        await self.channel_layer.group_send(
            f"room_{self.room_id}",
            {
                "type": "cursor_move",
                "id": self.id,
                "x": 0,
                "y": 0,
                "colour": self.colour,
            }
        )

        # ============================================================
        # Send full stroke history
        # ============================================================
        raw_strokes = await safe_redis(
            redis_client.lrange(f"strokes:{self.room_id}", 0, -1),
            []
        )
        strokes = [json.loads(s) for s in raw_strokes]

        await self.send(text_data=json.dumps({
            "strokes": strokes
        }))

        # ============================================================
        # Send snapshot of existing players
        # ============================================================
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

    async def disconnect(self, close_code):
        print("DISCONNECT:", self.room_id, self.id)
        # Remove position
        await safe_redis(redis_client.hdel(
            f"positions:{self.room_id}",
            self.id
        ))

        # Broadcast disconnect
        await safe_redis(redis_client.xadd(
            self.stream,
            {"id": self.id, "disconnect": "1"},
            maxlen=1000,
            approximate=True
        ))

        # Leave group
        await self.channel_layer.group_discard(
            f"room_{self.room_id}",
            self.channel_name
        )

        # Decrement connection count
        ROOM_CONNECTIONS[self.room_id] -= 1

        # Stop reader if last connection left
        if ROOM_CONNECTIONS[self.room_id] == 0:
            reader = ROOM_READERS.pop(self.room_id, None)
            if reader:
                reader.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        # ============================================================
        # SECURITY: ignore client-provided colour/diameter
        # ============================================================
        colour = self.colour
        diameter = self.diameter

        # ============================================================
        # 1. Stroke (drawing or click-dot)
        # ============================================================
        if "stroke" in data or data.get("draw"):
            if "stroke" in data:
                raw = data["stroke"]

                # SECURITY: sanitize stroke
                try:
                    stroke = {
                        "x1": int(raw.get("x1", 0)),
                        "y1": int(raw.get("y1", 0)),
                        "x2": int(raw.get("x2", 0)),
                        "y2": int(raw.get("y2", 0)),
                        "colour": colour,
                        "diameter": diameter
                    }
                except (KeyError, TypeError, ValueError):
                    return

            else:
                stroke = {
                    "x1": int(data.get("x", 0)),
                    "y1": int(data.get("y", 0)),
                    "x2": int(data.get("x", 0)),
                    "y2": int(data.get("y", 0)),
                    "colour": colour,
                    "diameter": diameter
                }

            # Store persistent stroke
            await safe_redis(redis_client.rpush(
                f"strokes:{self.room_id}",
                json.dumps(stroke)
            ))

            # Broadcast stroke via Redis stream
            await safe_redis(redis_client.xadd(
                self.stream,
                {"stroke": json.dumps(stroke)},
                maxlen=1000,
                approximate=True
            ))
            return

        # ============================================================
        # 2. Movement
        # ============================================================
        if "x" in data and "y" in data:
            try:
                x = int(data["x"])
                y = int(data["y"])
            except (KeyError, TypeError, ValueError):
                return

            await safe_redis(redis_client.hset(
                f"positions:{self.room_id}",
                self.id,
                f"{x},{y},{colour}"
            ))

            await safe_redis(redis_client.xadd(
                self.stream,
                {
                    "id": self.id,
                    "x": x,
                    "y": y,
                    "colour": colour
                },
                maxlen=1000,
                approximate=True
            ))

    # ============================================================
    # Group event handler
    # ============================================================
    async def room_event(self, event):
        fields = event["fields"]

        # Disconnect
        if "disconnect" in fields:
            await self.send(text_data=json.dumps({
                "id": fields["id"],
                "disconnect": True
            }))
            return

        # Stroke
        if "stroke" in fields:
            await self.send(text_data=json.dumps({
                "stroke": json.loads(fields["stroke"])
            }))
            return

        # Movement
        await self.send(text_data=json.dumps({
            "id": fields["id"],
            "x": fields["x"],
            "y": fields["y"],
            "colour": fields.get("colour", get_default_colour())
        }))
    
    # ============================================================
    # Called when the room owner loads a saved board.
    # Broadcasts a full reload event to the client.
    # ============================================================
    async def room_reload(self, event):
        strokes = event["strokes"]

        await self.send(text_data=json.dumps({
            "reload": True,
            "strokes": strokes
        }))
        
    async def cursor_move(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "x": event["x"],
            "y": event["y"],
            "colour": event.get("colour"),
            "diameter": event.get("diameter")
        }))
