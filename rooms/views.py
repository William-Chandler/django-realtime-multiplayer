import json
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from mysite.redis import redis_client
from whiteboards.state import (
    get_room_strokes,
    set_room_strokes,
    save_state_to_s3,
    load_state_from_s3,
    save_board_to_s3,
    load_board_from_s3,
    set_room_strokes
)
from whiteboards.models import SavedBoard
from .models import Room

def create_room(request):
    if request.method == "POST":
        room_id = request.POST["room_id"]
        password = request.POST["password"]

        room = Room(room_id=room_id, owner=request.user)
        room.set_password(password)
        room.save()

        return redirect(f"/rooms/{room_id}/")

    return render(request, "rooms/create_room.html")
    
def join_room(request):
    if request.method == "POST":
        room_id = request.POST["room_id"]
        password = request.POST["password"]

        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return render(request, "rooms/join_room.html", {"error": "Room not found"})

        if not room.check_password(password):
            return render(request, "rooms/join_room.html", {"error": "Incorrect password"})

        return redirect(f"/rooms/{room_id}/")

    return render(request, "rooms/join_room.html")
   
def room_page(request, room_id):
    room = Room.objects.get(room_id=room_id)
    return render(request, "rooms/room.html", {
        "room": room,
        "room_id": room.room_id,
    })

def user_can_access_room(request, room_id):
    try:
        Room.objects.get(room_id=room_id)
        return True
    except Room.DoesNotExist:
        return False


@require_POST
def save_room_state(request, room_id):
    if not user_can_access_room(request, room_id):
        return HttpResponseForbidden("No access to this room")

    # 1. Get strokes from Redis (sync wrapper)
    strokes = async_to_sync(get_room_strokes)(room_id) 

    # 2. Generate a unique board ID
    board_uuid = uuid.uuid4().hex

    # 3. Build the S3 key for user-level persistence
    s3_key = f"users/{request.user.id}/boards/{board_uuid}.json"

    # 4. Save to S3 (sync)
    save_board_to_s3(s3_key, strokes)

    # 5. Create DB entry (sync)
    board = SavedBoard.objects.create(
        owner=request.user,
        name=f"Board {board_uuid}",
        s3_key=s3_key,
    )

    return JsonResponse({
        "status": "ok",
        "saved_strokes": len(strokes),
        "board_id": board.id,
        "s3_key": s3_key,
    })



@require_GET
def load_room_state(request, room_id):
    # Validate room
    try:
        room = Room.objects.get(room_id=room_id)
    except Room.DoesNotExist:
        return HttpResponseForbidden("Room not found")

    # Only owner may load
    if room.owner != request.user:
        return HttpResponseForbidden("Only the room owner can load saved boards")

    # Load strokes from S3 (sync)
    strokes = load_state_from_s3(room_id)

    if strokes is None:
        return JsonResponse({"status": "empty"})

    # Hydrate Redis (async → sync)
    async_to_sync(set_room_strokes)(room_id, strokes)

    return JsonResponse({"status": "ok", "strokes":  strokes})
    
@require_POST
def load_user_board_into_room(request, room_id, board_id):
    # 1. Validate room
    try:
        room = Room.objects.get(room_id=room_id)
    except Room.DoesNotExist:
        return HttpResponseForbidden("Room not found")

    # 2. Only room owner may load boards
    if room.owner != request.user:
        return HttpResponseForbidden("Only the room owner can load boards")

    # 3. Validate board ownership
    try:
        board = SavedBoard.objects.get(id=board_id, owner=request.user)
    except SavedBoard.DoesNotExist:
        return HttpResponseForbidden("Board not found or not owned by user")

    # 4. Load strokes from S3 (sync)
    strokes = load_board_from_s3(board.s3_key)

    if strokes is None:
        return JsonResponse({"status": "error", "message": "Board file missing"})

    # 5. Hydrate Redis (async → sync)
    async_to_sync(set_room_strokes)(room_id, strokes)

    # 6. Broadcast reload event (async → sync)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room_id}",
        {
            "type": "room.reload",
            "strokes": strokes,
        }
    )

    return JsonResponse({
        "status": "ok",
        "loaded_strokes": len(strokes),
        "board_name": board.name,
    })



