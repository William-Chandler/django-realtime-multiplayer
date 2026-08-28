import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_index_view_renders_template(client):
    url = reverse("index")
    response = client.get(url)

    assert response.status_code == 200
    assert "core/index.html" in [t.name for t in response.templates]
