# whiteboards/models.py

from django.db import models
from django.conf import settings

class SavedBoard(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    s3_key = models.CharField(max_length=256)   # e.g. "users/42/boards/abc123.json"
    created_at = models.DateTimeField(auto_now_add=True)
