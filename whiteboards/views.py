import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from .models import SavedBoard
from rooms.models import Room
from .state import get_room_strokes, save_board_to_s3

@login_required
def my_boards(request):
    boards = SavedBoard.objects.filter(owner=request.user).order_by("-created_at")

    data = [
        {
            "id": board.id,
            "name": board.name,
            "created_at": board.created_at.isoformat()
        }
        for board in boards
    ]

    return JsonResponse(data, safe=False)
    
@login_required
def save_whiteboard(request, room_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    payload = json.loads(request.body.decode("utf-8"))
    board_name = payload.get("name", "").strip()
    overwrite = payload.get("overwrite", False)

    if not board_name:
        return JsonResponse({"error": "Missing board name"}, status=400)

    # Check if board already exists
    existing = SavedBoard.objects.filter(owner=request.user, name=board_name).first()

    if existing and not overwrite:
        # Tell frontend: board exists, ask user for confirmation
        return JsonResponse({"exists": True})

    # Get strokes from Redis
    strokes = async_to_sync(get_room_strokes)(room_id)

    safe_name = board_name.replace(" ", "_")
    s3_key = f"users/{request.user.id}/boards/{safe_name}.json"

    # Save to S3
    save_board_to_s3(s3_key, strokes)

    if existing:
        # Overwrite existing DB entry
        existing.s3_key = s3_key
        existing.save()
        return JsonResponse({"status": "ok", "id": existing.id, "overwritten": True})

    # Create new board
    board = SavedBoard.objects.create(
        owner=request.user,
        name=board_name,
        s3_key=s3_key
    )

    return JsonResponse({"status": "ok", "id": board.id, "created": True})

