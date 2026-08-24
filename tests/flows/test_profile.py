import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_hacker_can_view_profile(hacker_client):
    client, user = hacker_client

    response = client.get(reverse("user_profile"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_hacker_can_update_name(hacker_client):
    client, user = hacker_client

    response = client.post(reverse("user_profile"), data={"name": "Gerard Màdrid", "type": "H"})

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.name == "Gerard Màdrid"
