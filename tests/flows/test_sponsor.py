import pytest
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from applications.models.sponsor import SponsorApplication
from user.models import Token
from tests.factories import SponsorUserFactory

VALID_SPONSOR_FORM = {
    "name": "Jane Doe",
    "email": "jane.doe@techcorp.com",
    "attendance": ["1"],
    "diet": "None",
    "tshirt_size": "M",
    "phone_number": "+34600000000",
    "position": "Software Engineer",
    "terms_and_conditions": True,
}


@pytest.mark.django_db
def test_sponsor_can_view_dashboard(sponsor_client):
    client, user = sponsor_client
    response = client.get(reverse("sponsor_dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_sponsor_can_submit_application(db):
    sponsor_user = SponsorUserFactory()
    token_obj = Token.objects.create(user=sponsor_user)
    uid = urlsafe_base64_encode(force_bytes(sponsor_user.pk))
    token = token_obj.uuid_str()
    url = f"/sponsor/{uid}/{token}/"
    client = Client()
    response = client.post(url, data=VALID_SPONSOR_FORM)
    if response.status_code != 200:
        print(response.context['form'].errors)
    # View renders sponsor_submitted.html on success (200, not 302)
    assert response.status_code == 200
    assert SponsorApplication.objects.count() == 1


@pytest.mark.django_db
def test_organizer_can_view_sponsor_list(director_client):
    client, _ = director_client
    response = client.get(reverse("sponsor_list"))
    assert response.status_code == 200
