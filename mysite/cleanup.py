import asyncio
import time
from mysite.redis import get_redis_client
from rooms.services import delete_room
import redis.exceptions

async def room_cleanup_loop():
    redis = get_redis_client()
    print("CLEANUP LOOP STARTED")

    while True:
        try:
            # Safe read of active rooms
            room_ids = await safe_redis(redis.smembers("rooms:active"), [])
            now = int(time.time())

            for room_id in room_ids:
                # Safe read of connection count
                connections = await safe_redis(
                    redis.get(f"room:{room_id}:connections"),
                    None
                )

                if connections is None:
                    continue

                try:
                    if int(connections) > 0:
                        continue
                except:
                    continue

                # Safe read of last_empty timestamp
                last_empty = await safe_redis(
                    redis.get(f"room:{room_id}:last_empty"),
                    None
                )

                if last_empty is None:
                    continue

                try:
                    last_empty = int(last_empty)
                except:
                    continue

                # Room inactive long enough → delete
                if now - last_empty > 60:
                    print(f"CLEANING