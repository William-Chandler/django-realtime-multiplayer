import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages


# ---------------------------------------------------------------------
# SIGNUP VIEW
# ---------------------------------------------------------------------

@pytest.mark.django_db
def test_signup_get_renders_template(client):
    response = client.get(reverse("signup"))
    assert response.status_code == 200
    assert "accounts/signup.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_signup_redirects_if_logged_in(client):
    user = User.objects.create_user(username="alice", password="pass")
    client.login(username="alice", password="pass")

    response = client.get(reverse("signup"))
    assert response.status_code == 200
    assert "accounts/already_logged_in.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_signup_password_mismatch(client):
    response = client.post(reverse("signup"), {
        "username": "bob",
        "email": "bob@example.com",
        "password": "abc",
        "password2": "xyz",
    })

    assert response.status_code == 302
    assert response.url == reverse("signup")

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "Passwords do not match" in messages


@pytest.mark.django_db
def test_signup_username_taken(client):
    User.objects.create_user(username="bob", password="pass")

    response = client.post(reverse("signup"), {
        "username": "bob",
        "email": "bob@example.com",
        "password": "abc",
        "password2": "abc",
    })

    assert response.status_code == 302
    assert response.url == reverse("signup")

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "Username already taken" in messages


@pytest.mark.django_db
def test_signup_success_creates_user_and_logs_in(client):
    response = client.post(reverse("signup"), {
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "abc",
        "password2": "abc",
    })

    assert response.status_code == 302
    assert response.url == reverse("index")

    user = User.objects.get(username="charlie")
    assert user.is_authenticated

    # Client should now be logged in
    assert client.session["_auth_user_id"] == str(user.id)


# ---------------------------------------------------------------------
# LOGIN VIEW
# ---------------------------------------------------------------------

@pytest.mark.django_db
def test_login_get_renders_template(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert "accounts/login.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_login_redirects_if_logged_in(client):
    user = User.objects.create_user(username="alice", password="pass")
    client.login(username="alice", password="pass")

    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert "accounts/already_logged_in.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    response = client.post(reverse("login"), {
        "username": "nope",
        "password": "wrong",
    })

    assert response.status_code == 302
    assert response.url == reverse("login")

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "Invalid credentials" in messages


@pytest.mark.django_db
def test_login_success(client):
    User.objects.create_user(username="dave", password="pass")

    response = client.post(reverse("login"), {
        "username": "dave",
        "password": "pass",
    })

    assert response.status_code == 302
    assert response.url == reverse("index")

    user = User.objects.get(username="dave")
    assert client.session["_auth_user_id"] == str(user.id)


# ---------------------------------------------------------------------
# LOGOUT VIEW
# ---------------------------------------------------------------------

@pytest.mark.django_db
def test_logout_logs_out_and_redirects(client):
    user = User.objects.create_user(username="eve", password="pass")
    client.login(username="eve", password="pass")

    response = client.get(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("index")

    assert "_auth_user_id" not in client.session


# ---------------------------------------------------------------------
# PREFERENCES VIEW
# ---------------------------------------------------------------------

@pytest.mark.django_db
def test_preferences_requires_login(client):
    response = client.get(reverse("preferences"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_preferences_get_renders_template(client):
    user = User.objects.create_user(username="frank", password="pass")
    client.login(username="frank", password="pass")

    response = client.get(reverse("preferences"))
    assert response.status_code == 200
    assert "accounts/preferences.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_preferences_updates_colour_and_redirects(client):
    user = User.objects.create_user(username="gina", password="pass")
    client.login(username="gina", password="pass")

    response = client.post(reverse("preferences"), {
        "colour_preference": "blue",
        "next": "/custom/",
    })

    assert response.status_code == 302
    assert response.url == "/custom/"

    user.refresh_from_db()
    assert user.userprofile.colour_preference == "blue"


@pytest.mark.django_db
def test_preferences_redirects_to_root_if_no_next(client):
    user = User.objects.create_user(username="henry", password="pass")
    client.login(username="henry", password="pass")

    response = client.post(reverse("preferences"), {
        "colour_preference": "green",
    })

    assert response.status_code == 302
    assert response.url == "/"

    user.refresh_from_db()
    assert user.userprofile.colour_preference == "green"
