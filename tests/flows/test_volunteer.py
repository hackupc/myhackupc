import pytest
from django.urls import reverse

from applications.models import APP_CANCELLED, APP_CONFIRMED, APP_INVITED, APP_PENDING
from applications.models.volunteer import VolunteerApplication
from tests.factories import VolunteerApplicationFactory

VALID_VOLUNTEER_FORM = {
    "gender": "NA",
    "under_age": "False",
    "studies_and_course": "Computer Science",
    "night_shifts": "No",
    "first_time_volunteer": "True",
    "diet": "None",
    "tshirt_size": "M",
    "origin": "Barcelona, Barcelona, Spain",
    "hear_about_us": "Posters",
    "terms_and_conditions": True,
    "attendance": ["1"],
    "languages": ["English"],
    "quality": "Team player",
    "weakness": "Perfectionist",
    "cool_skill": "Python",
    "volunteer_motivation": "I want to help hackers succeed.",
    "graduation_year": "2026",
}


@pytest.mark.django_db
def test_volunteer_can_view_dashboard(volunteer_client):
    client, user = volunteer_client
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_volunteer_can_submit_application(volunteer_client):
    client, user = volunteer_client
    response = client.post(reverse("dashboard"), data=VALID_VOLUNTEER_FORM)
    if response.status_code != 302:
        print(response.context['form'].errors)
    assert response.status_code == 302
    assert VolunteerApplication.objects.filter(user=user, status=APP_PENDING).exists()


@pytest.mark.django_db
def test_volunteer_can_cancel_invited(volunteer_client):
    client, user = volunteer_client
    app = VolunteerApplicationFactory(user=user, status=APP_INVITED)
    response = client.post(reverse("cancel_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_CANCELLED


@pytest.mark.django_db
def test_invited_volunteer_can_confirm(volunteer_client):
    client, user = volunteer_client
    app = VolunteerApplicationFactory(user=user, status=APP_INVITED)
    response = client.get(reverse("confirm_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_CONFIRMED


@pytest.mark.django_db
def test_organizer_can_view_volunteer_list(organizer_client):
    client, _ = organizer_client
    response = client.get(reverse("volunteer_list"))
    assert response.status_code == 200
