from django.urls import URLPattern, URLResolver
from django.urls.resolvers import RegexPattern
from mysite.urls import urlpatterns
from core.views import index


def get_non_static_urlpatterns():
    patterns = []
    for p in urlpatterns:
        # Skip Django's static() patterns (RegexPattern)
        if isinstance(p.pattern, RegexPattern):
            if p.pattern.regex.pattern.startswith("^static/"):
                continue
        patterns.append(p)
    return patterns


def test_urlpatterns_count():
    patterns = get_non_static_urlpatterns()
    assert len(patterns) == 5


def test_core_include():
    patterns = get_non_static_urlpatterns()
    route = patterns[0]

    assert isinstance(route, URLResolver)
    assert route.pattern._route == ""
    assert route.urlconf_module.__name__.endswith("core.urls")


def test_home_route():
    patterns = get_non_static_urlpatterns()
    route = patterns[1]

    assert isinstance(route, URLPattern)
    assert route.pattern._route == ""
    assert route.name == "home"
    assert route.callback is index


def test_accounts_include():
    patterns = get_non_static_urlpatterns()
    route = patterns[2]

    assert isinstance(route, URLResolver)
    assert route.pattern._route == "accounts/"
    assert route.urlconf_module.__name__.endswith("accounts.urls")


def test_rooms_include():
    patterns = get_non_static_urlpatterns()
    route = patterns[3]

    assert isinstance(route, URLResolver)
    assert route.pattern._route == "rooms/"
    assert route.urlconf_module.__name__.endswith("rooms.urls")


def test_whiteboards_include():
    patterns = get_non_static_urlpatterns()
    route = patterns[4]

    assert isinstance(route, URLResolver)
    assert route.pattern._route == "whiteboards/"
    assert route.urlconf_module.__name__.endswith("whiteboards.urls")
