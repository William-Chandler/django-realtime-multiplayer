import asyncio
import time
from mysite.redis import redis_client
from rooms.services import delete_room

async def room_cleanup_loop():
    while True:
        now = int(time.time())

        # get all rooms we’re tracking
        room_ids = await redis_client.smembers("rooms:active")

        for room_id in room_ids:
            # connections
            connections = await redis_client.get(f"room:{room_id}:connections")
            if connections is None or int(connections) > 0:
                continue

            # last empty time
            last_empty = await redis_client.get(f"room:{room_id}:last_empty")
            if last_empty is None:
                continue

            # inactive for > 60 seconds
            if now - int(last_empty) > 60:
                await delete_room(room_id)

                # cleanup Redis keys
                await redis_client.delete(
                    f"room:{room_id}:connections",
                    f"room:{room_id}:last_empty",
                )
                await redis_client.srem("rooms:active", room_id)

        await asyncio.sleep(5)