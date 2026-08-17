from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_room, name="create_room"),
    path("join/", views.join_room, name="join_room"),
    path("<room_id>/", views.room_page, name="room_page"),

    # New API endpoints
    path("<room_id>/save/", views.save_room_state, name="save_room_state"),
    path("<room_id>/load/", views.load_room_state, name="load_room_state"),
    path("<room_id>/load_board/<int:board_id>/", views.load_user_board_into_room),
    
]