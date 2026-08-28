from django.contrib import admin
from accounts.models import UserProfile


def test_userprofile_is_registered_in_admin():
    # admin.site._registry is a dict: {model_class: admin_class_instance}
    assert UserProfile in admin.site._registry

    # Ensure it uses the default ModelAdmin
    model_admin = admin.site._registry[UserProfile]
    assert model_admin.__class__.__name__ == "ModelAdmin"
