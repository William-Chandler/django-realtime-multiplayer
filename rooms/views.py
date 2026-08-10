from django.shortcuts import render, redirect
from .models import Room

def create_room(request):
    if request.method == "POST":
        room_id = request.POST["room_id"]
        password = request.POST["password"]

        room = Room(room_id=room_id)
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



