import pytest
from django.conf import settings
from core.consumers import get_default_diameter

def test_get_default_diameter_custom(settings):
    settings.DEFAULT_DIAMETER = 42
    assert get_default_diameter() == 42

def test_get_default_diameter_default(settings):
    if hasattr(settings, "DEFAULT_DIAMETER"):
        del settings.DEFAULT_DIAMETER
    assert get_default_diameter() == 10
