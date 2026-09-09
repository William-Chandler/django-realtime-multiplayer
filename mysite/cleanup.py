import asyncio
import time
from mysite.redis import get_redis_client
from rooms.services import delete_room
from core.consumers import safe_redis

async def room_cleanup_loop():
    redis = get_redis_client()
    print("CLEANUP LOOP STARTED")

    while True:
        try:
            # Safely read active rooms
            room_ids = await safe_redis(redis.smembers("rooms:active"), [])
            now = int(time.time())

            for room_id in room_ids:
                # Safely read connection count
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

                # Safely read last_empty timestamp
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
                    print(f"CLEANING ROOM {room_id}")

                    await delete_room(room_id)

                    # Safely delete Redis keys
                    await safe_redis(redis.delete(
                        f"room:{room_id}:connections",
                        f"room:{room_id}:last_empty",
                    ))

                    await safe_redis(redis.srem("rooms:active", room_id))

        except Exception as e:
            print(f"CLEANUP LOOP ERROR: {e}")

        await asyncio.sleep(5)
