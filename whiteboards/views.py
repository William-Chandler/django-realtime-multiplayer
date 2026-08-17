from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import SavedBoard

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
