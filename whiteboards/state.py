# whiteboards/state.py

import json
from django.core.files.base import ContentFile
from .storage import WhiteboardStorage
from mysite.redis import redis_client

storage = WhiteboardStorage()

async def get_room_strokes(room_id):
    raw_strokes = await redis_client.lrange(f"strokes:{room_id}", 0, -1)
    return [json.loads(s) for s in raw_strokes]

async def set_room_strokes(room_id, strokes):
    # Clear existing strokes
    await redis_client.delete(f"strokes:{room_id}")
    if strokes:
        for s in strokes:
            await redis_client.rpush(f"strokes:{room_id}", json.dumps(s))

# Room-level persistence
def s3_key_for_room_state(room_id):
    return f"rooms/{room_id}/state.json"
    
# User-level persistence
def s3_key_for_user_board(user_id, board_uuid):
    return f"users/{user_id}/boards/{board_uuid}.json"

# Use this for user-saved boards
def save_board_to_s3(s3_key, strokes):
    payload = json.dumps({"strokes": strokes})
    storage.save(s3_key, ContentFile(payload.encode("utf-8")))

# ONLY for autosave functionality
def save_state_to_s3(room_id, strokes):
    payload = json.dumps({"strokes": strokes})
    key = s3_key_for_room_state(room_id)
    storage.save(key, ContentFile(payload.encode("utf-8")))

def load_state_from_s3(room_id):
    key = s3_key_for_room_state(room_id)
    if not storage.exists(key):
        return None

    with storage.open(key, "r") as f:
        data = json.load(f)
    return data.get("strokes", [])
    
def load_board_from_s3(s3_key):
    if not storage.exists(s3_key):
        return None

    with storage.open(s3_key, "r") as f:
        data = json.load(f)

    return data.get("strokes", [])

