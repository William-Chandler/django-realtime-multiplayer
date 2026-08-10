from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Room(models.Model):
    room_id = models.CharField(max_length=64, unique=True)
    password_hash = models.CharField(max_length=128)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)
