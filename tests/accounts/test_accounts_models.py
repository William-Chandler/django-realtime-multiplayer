import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from accounts.models import UserProfile


@pytest.mark.django_db
def test_userprofile_is_created_automatically():
    user = User.objects.create(username="alice")
    profile = UserProfile.objects.get(user=user)

    assert profile.colour_preference == "red"  # default


def test_colour_preference_field_properties():
    field = UserProfile._meta.get_field("colour_preference")

    assert field.max_length == 20
    assert field.default == "red"
    assert field.choices == UserProfile.COLOUR_CHOICES


@pytest.mark.django_db
def test_userprofile_accepts_valid_choice():
    user = User.objects.create(username="bob")
    profile = user.userprofile  # auto-created

    profile.colour_preference = "blue"
    profile.full_clean()  # should not raise
    profile.save()

    assert profile.colour_preference == "blue"


@pytest.mark.django_db
def test_userprofile_rejects_invalid_choice():
    user = User.objects.create(username="charlie")
    profile = user.userprofile  # auto-created

    profile.colour_preference = "not-a-colour"

    with pytest.raises(ValidationError):
        profile.full_clean()
