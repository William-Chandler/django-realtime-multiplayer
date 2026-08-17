from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


class Room(models.Model):
    room_id = models.CharField(max_length=64, unique=True)
    password_hash = models.CharField(max_length=128)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)
