import pytest
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models.signals import post_save

from accounts.models import UserProfile
from accounts import signals


@pytest.mark.django_db
def test_create_user_profile_signal_creates_profile():
    # Ensure no profiles exist yet
    assert UserProfile.objects.count() == 0

    user = User.objects.create(username="alice")

    # Signal should have created exactly one profile
    assert UserProfile.objects.count() == 1

    profile = UserProfile.objects.get(user=user)
    assert profile.colour_preference == "red"  # default


@pytest.mark.django_db
def test_save_user_profile_signal_called_on_user_save():
    user = User.objects.create(username="bob")
    profile = user.userprofile

    with patch.object(UserProfile, "save") as mock_save:
        user.save()
        mock_save.assert_called_once()


def test_signals_are_connected():
    # Ensure both receivers are registered for User.post_save
    receivers = [r[1]() for r in post_save.receivers]

    assert signals.create_user_profile in receivers
    assert signals.save_user_profile in receivers
