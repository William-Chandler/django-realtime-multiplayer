from django.urls import path
from . import views

urlpatterns = [
    path("api/my_boards/", views.my_boards, name="my_boards"),
]
