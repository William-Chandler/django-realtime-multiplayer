from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    COLOUR_CHOICES = [
        ("red", "Red"),
        ("blue", "Blue"),
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("purple", "Purple"),
        ("orange", "Orange"),
        ("pink", "Pink"),
        ("white", "White"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    colour_preference = models.CharField(
        max_length=20,
        choices=COLOUR_CHOICES,
        default="red",
    )

