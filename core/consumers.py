import json
import uuid
import asyncio
import time
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from mysite.redis import get_redis_client
from django.conf import settings
from whiteboards.state import load_state_from_s3

redis_client = get_redis_client()
ROOM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

# ============================================================
# Start cleanup process
# ============================================================

cleanup_started = False

async def start_cleanup():
    from mysite.cleanup import room_cleanup_loop
    global cleanup_started
    if not cleanup_started:
        print("STARTING CLEANUP LOOP")
        cleanup_started = True
        asyncio.create_task(room_cleanup_loop())

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
    print("READER for room_id", room_id)
    channel_layer = get_channel_layer()
    stream = f"game:room:{room_id}"

    # Start from new messages only
    last_id = "0"

    try:
        while True:
            try:
                entries = await redis_client.xread(
                    {stream: last_id},
                    block=1000,
                    count=10
                )
            except asyncio.CancelledError:
                # Reader was cancelled intentionally
                print("READER CANCELLED:", room_id)
                break
            except Exception as e:
                print("XREAD ERROR:", e)
                await asyncio.sleep(0.1)
                continue

            if not entries:
                await asyncio.sleep(0.05)
                continue

            _, messages = entries[0]

            for msg_id, fields in messages:
                last_id = msg_id

                # SECURITY: validate fields
                if not isinstance(fields, dict):
                    continue

                await channel_layer.group_send(
                    f"room_{room_id}",
                    {
                        "type": "room.event",
                        "fields": fields
                    }
                )

    finally:
        print("READER EXITING CLEANLY:", room_id)



# ============================================================
# WebSocket Consumer
# ============================================================

class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await start_cleanup()

        # Validate room_id
        raw_room_id = self.scope["url_route"]["kwargs"]["room_id"]
        if not ROOM_ID_RE.match(raw_room_id):
            await self.close()
            return
            
        # Defensive attributes in case connect partially fails
        self.room_id = None
        self.id = None
        self.stream = None
        self.reader_task = None

        self.room_id = raw_room_id
        self.id = str(uuid.uuid4())
        self.stream = f"game:room:{self.room_id}"

        # Mark player as connected (per-connection flag in Redis)
        await safe_redis(redis_client.set(f"player:{self.id}:connected", "1"))

        # Authentication / identity
        user = self.scope["user"]

        if getattr(user, "is_anonymous", False):
            # Anonymous: defaults
            self.colour = get_default_colour()
            self.diameter = get_default_diameter()
        else:
            # Logged-in: use profile if available
            profile = await database_sync_to_async(
                lambda: getattr(user, "userprofile", None)
            )()
            if profile:
                self.colour = await database_sync_to_async(
                    lambda: getattr(profile, "colour_preference", get_default_colour())
                )()
                self.diameter = await database_sync_to_async(
                    lambda: getattr(profile, "diameter_preference", get_default_diameter())
                )()
            else:
                self.colour = get_default_colour()
                self.diameter = get_default_diameter()

        # Track room in Redis
        await safe_redis(redis_client.sadd("rooms:active", self.room_id))
        connections = await safe_redis(
            redis_client.incr(f"room:{self.room_id}:connections")
        )

        # Cluster-safe reader startup (no ROOM_READERS)
        started = await safe_redis(
            redis_client.setnx(f"room:{self.room_id}:reader_running", "1")
        )

        if started:
            # Store reader task on this consumer instance
            self.reader_task = asyncio.create_task(
                room_stream_reader(self.room_id)
            )
        else:
            self.reader_task = None

        # Join Channels group
        await self.channel_layer.group_add(
            f"room_{self.room_id}",
            self.channel_name
        )

        await self.accept()

        # Store initial position
        await safe_redis(redis_client.hset(
            f"positions:{self.room_id}",
            self.id,
            f"0,0,{self.colour}"
        ))

        # Broadcast initial cursor
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

        # Send stroke history (bounded)
        MAX_STROKES = 5000
        raw_strokes = await safe_redis(
            redis_client.lrange(f"strokes:{self.room_id}", 0, MAX_STROKES - 1),
            []
        )
        strokes = [json.loads(s) for s in raw_strokes]
        await self.send(text_data=json.dumps({"strokes": strokes}))

        # Send snapshot of existing players
        positions = await safe_redis(
            redis_client.hgetall(f"positions:{self.room_id}"),
            {}
        )

        for pid, pos in positions.items():
            # Only include players still marked as connected
            connected = await safe_redis(
                redis_client.get(f"player:{pid}:connected"),
                "0"
            )
            if connected != "1":
                continue

            try:
                x, y, colour = pos.split(",")
            except Exception:
                continue

            await self.send(text_data=json.dumps({
                "id": pid,
                "x": int(x),
                "y": int(y),
                "colour": colour
            }))



    async def disconnect(self, close_code):
        print("DISCONNECT:", self.room_id, self.id)
        
        # Defensive guard
        if not getattr(self, "room_id", None) or not getattr(self, "id", None):
            return


        # Clear per-player connected flag
        await safe_redis(redis_client.delete(f"player:{self.id}:connected"))

        # Remove position from Redis
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

        # Leave Channels group
        await self.channel_layer.group_discard(
            f"room_{self.room_id}",
            self.channel_name
        )

        # Decrement connection count
        new_count = int(await safe_redis(
            redis_client.decr(f"room:{self.room_id}:connections"),
            0
        ))

        # Clamp to 0 if something went wrong
        if new_count < 0:
            new_count = 0
            await safe_redis(redis_client.set(
                f"room:{self.room_id}:connections",
                0
            ))

        # If room is now empty, stop reader and clear lock
        if new_count == 0:
            print("SETTING LAST_EMPTY FOR", self.room_id)
            await safe_redis(redis_client.set(
                f"room:{self.room_id}:last_empty",
                int(time.time())
            ))
            print("LAST_EMPTY SET, new_count =", new_count)

            # Cancel reader task if this consumer started it
            if getattr(self, "reader_task", None):
                self.reader_task.cancel()

            # Clear Redis reader lock so next connection can start a reader
            await safe_redis(redis_client.delete(
                f"room:{self.room_id}:reader_running"
            ))




    async def receive(self, text_data):
        # Heartbeat
        if text_data == "ping":
            await self.send("pong")
            return
            
        # Prevent malicious clients sending huge payloads
        if len(text_data) > 4096:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        # SECURITY: ignore client-provided colour/diameter
        colour = self.colour
        diameter = self.diameter

        # Helper: clamp coordinates to safe range
        def clamp(v, lo=0, hi=2000):
            try:
                return max(lo, min(hi, int(v)))
            except Exception:
                return lo

        # ------------------------------------------------------------
        # 1. Stroke (drawing or click-dot)
        # ------------------------------------------------------------
        if "stroke" in data or data.get("draw"):
            # SECURITY: stroke rate limiting
            now = time.monotonic()
            if hasattr(self, "_last_stroke"):
                if now - self._last_stroke < 0.002:  # 500 strokes/sec max
                    return
            self._last_stroke = now
            if "stroke" in data:
                raw = data["stroke"]

                try:
                    stroke = {
                        "x1": clamp(raw.get("x1", 0)),
                        "y1": clamp(raw.get("y1", 0)),
                        "x2": clamp(raw.get("x2", 0)),
                        "y2": clamp(raw.get("y2", 0)),
                        "colour": colour,
                        "diameter": diameter
                    }
                except Exception:
                    return

            else:
                stroke = {
                    "x1": clamp(data.get("x", 0)),
                    "y1": clamp(data.get("y", 0)),
                    "x2": clamp(data.get("x", 0)),
                    "y2": clamp(data.get("y", 0)),
                    "colour": colour,
                    "diameter": diameter
                }

            # SECURITY: limit stroke length
            dx = abs(stroke["x2"] - stroke["x1"])
            dy = abs(stroke["y2"] - stroke["y1"])
            if dx > 2000 or dy > 2000:
                return

            # SECURITY: limit total strokes
            MAX_STROKES = 5000
            count = int(await safe_redis(redis_client.llen(f"strokes:{self.room_id}"), 0))
            if count >= MAX_STROKES:
                return


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

        # ------------------------------------------------------------
        # 2. Movement
        # ------------------------------------------------------------
        if "x" in data and "y" in data:
            x = clamp(data.get("x"))
            y = clamp(data.get("y"))

            # SECURITY: movement rate limiting
            now = time.monotonic()
            if hasattr(self, "_last_move"):
                if now - self._last_move < 0.01:  # 100 moves/sec max
                    return
            self._last_move = now

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
        fields = event.get("fields", {})

        # Disconnect event
        if "disconnect" in fields:
            await self.send(text_data=json.dumps({
                "id": fields.get("id"),
                "disconnect": True
            }))
            return

        # Stroke event
        if "stroke" in fields:
            try:
                stroke = json.loads(fields["stroke"])
            except Exception:
                return

            await self.send(text_data=json.dumps({
                "stroke": stroke
            }))
            return

        # Movement event
        if "x" in fields and "y" in fields:
            try:
                x = int(fields["x"])
                y = int(fields["y"])
            except Exception:
                return

            await self.send(text_data=json.dumps({
                "id": fields.get("id"),
                "x": x,
                "y": y,
                "colour": fields["colour"]
            }))
            return

        # Unknown event type — ignore safely
        return

    
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
