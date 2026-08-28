import pytest
from django.conf import settings
from core.consumers import get_default_colour

def test_get_default_colour(settings):
    settings.DEFAULT_COLOUR = "#ff0000"
    assert get_default_colour() == "#ff0000"
