import asyncio
from channels.db import database_sync_to_async
from mysite.redis import get_redis_client
from rooms.models import Room
from whiteboards.state import delete_room_state_from_s3

async def delete_room(room_id):  
    # Redis cleanup
    redis = get_redis_client()
    await redis.delete(f"positions:{room_id}")
    await redis.delete(f"strokes:{room_id}")
    await redis.delete(f"game:room:{room_id}")

    # DB cleanup
    await database_sync_to_async(Room.objects.filter(room_id=room_id).delete)()

    # S3 cleanup
    await database_sync_to_async(delete_room_state_from_s3)(room_id)
    
async def purge_all_rooms():
    """
    Remove ALL ephemeral rooms from DB, Redis, and S3.
    Called on server startup.
    """
    print("🔥 purge_all_rooms() started")
    # Wait for redis and MinIO
    await wait_for_services()

    # Fetch all room IDs from D
    room_ids = await database_sync_to_async(
        list
    )(Room.objects.values_list("room_id", flat=True))

    print(f"🔥 purge_all_rooms() found room_ids: {room_ids}")

    if not room_ids:
        return

    redis = get_redis_client()

    # Delete Redis keys
    # We batch-delete keys for performance
    keys = []
    for room_id in room_ids:
        keys.extend([
            f"positions:{room_id}",
            f"strokes:{room_id}",
            f"game:room:{room_id}",
        ])

    await redis.delete(*keys)

    # --- Delete S3 autosave state ---
    for room_id in room_ids:
        await database_sync_to_async(delete_room_state_from_s3)(room_id)

    # --- Delete DB rows ---
    await database_sync_to_async(Room.objects.all().delete)()

async def wait_for_services():
    redis = get_redis_client()

    # Wait for Redis
    for _ in range(20):
        try:
            await redis.ping()
            break
        except Exception:
            await asyncio.sleep(0.5)

    # Wait for MinIO
    from whiteboards.state import get_storage

    storage = get_storage()

    for _ in range(20):
        try:
            # Try a harmless operation to confirm MinIO is reachable
            storage.exists("rooms/__startup_test__")
            break
        except Exception:
            await asyncio.sleep(0.5)

