import asyncio
import time
from mysite.redis import get_redis_client
from rooms.services import delete_room

async def room_cleanup_loop():
    redis = get_redis_client()
    while True:
        now = int(time.time())

        # get all rooms we’re tracking
        room_ids = await redis.smembers("rooms:active")

        for room_id in room_ids:
            # connections
            connections = await redis.get(f"room:{room_id}:connections")
            if connections is None or int(connections) > 0:
                continue

            # last empty time
            last_empty = await redis.get(f"room:{room_id}:last_empty")
            if last_empty is None:
                continue

            # inactive for > 60 seconds
            if now - int(last_empty) > 60:
                await delete_room(room_id)

                # cleanup Redis keys
                await redis.delete(
                    f"room:{room_id}:connections",
                    f"room:{room_id}:last_empty",
                )
                await redis.srem("rooms:active", room_id)

        await asyncio.sleep(5)