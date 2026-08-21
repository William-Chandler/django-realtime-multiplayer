from mysite.redis import redis_client
from channels.db import database_sync_to_async
from rooms.models import Room
from whiteboards.state import delete_room_state_from_s3

async def delete_room(room_id):
    # Redis cleanup
    await redis_client.delete(f"positions:{room_id}")
    await redis_client.delete(f"strokes:{room_id}")
    await redis_client.delete(f"game:room:{room_id}")

    # DB cleanup
    await database_sync_to_async(Room.objects.filter(room_id=room_id).delete)()

    # S3 cleanup
    await database_sync_to_async(delete_room_state_from_s3)(room_id)
