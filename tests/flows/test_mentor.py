import pytest
from django.urls import reverse

from applications.models import APP_CANCELLED, APP_CONFIRMED, APP_INVITED, APP_PENDING
from applications.models.mentor import MentorApplication
from tests.factories import MentorApplicationFactory

VALID_MENTOR_FORM = {
    "gender": "NA",
    "under_age": "False",
    "study_work": "True",
    "english_level": "3",
    "attendance": ["1"],
    "tshirt_size": "M",
    "diet": "None",
    "origin": "Barcelona, Barcelona, Spain",
    "linkedin": "https://www.linkedin.com/in/testmentor",
    "fluent": "Python, JavaScript",
    "experience": "5 years of software development.",
    "why_mentor": "I want to share my knowledge with students.",
    "participated": "HackUPC 2023",
    "terms_and_conditions": True,
    "degree": "Computer Science",
    "graduation_year": "2026",
    "first_timer": True,
    "lennyface": "( ͡° ͜ʖ ͡°)",
    "online": False,
}


@pytest.mark.django_db
def test_mentor_can_view_dashboard(mentor_client):
    client, user = mentor_client
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_mentor_can_submit_application(mentor_client):
    client, user = mentor_client
    response = client.post(reverse("dashboard"), data=VALID_MENTOR_FORM)
    if response.status_code != 302:
        print(response.context['form'].errors)
    assert response.status_code == 302
    assert MentorApplication.objects.filter(user=user, status=APP_PENDING).exists()


@pytest.mark.django_db
def test_mentor_can_cancel_invited(mentor_client):
    client, user = mentor_client
    app = MentorApplicationFactory(user=user, status=APP_INVITED)
    response = client.post(reverse("cancel_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_CANCELLED


@pytest.mark.django_db
def test_invited_mentor_can_confirm(mentor_client):
    client, user = mentor_client
    app = MentorApplicationFactory(user=user, status=APP_INVITED)
    response = client.get(reverse("confirm_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_CONFIRMED


@pytest.mark.django_db
def test_organizer_can_view_mentor_list(director_client):
    client, _ = director_client
    response = client.get(reverse("mentor_list"))
    assert response.status_code == 200
