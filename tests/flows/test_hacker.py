import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from applications.models import APP_CANCELLED, APP_CONFIRMED, APP_INVITED, APP_PENDING
from applications.models.hacker import HackerApplication
from organizers.models import Vote
from tests.factories import HackerApplicationFactory

VALID_HACKER_FORM = {
    "phone_number": "+34600000000",
    "kind_studies": "BACHELOR",
    "under_age": "False",
    "terms_and_conditions": True,
    "diet": "None",
    "tshirt_size": "M",
    "origin": "Barcelona, Barcelona, Spain",
    "description": "I want to build things at a hackathon.",
    "graduation_year": "2026",
    "gender": "NA",
    "first_timer": True,
    "lennyface": "( ͡° ͜ʖ ͡°)",
    "online": False,
    "university": "Universitat Politècnica de Catalunya",
    "degree": "Computer Science",
    "discover": "3",
}


@pytest.mark.django_db
def test_unauthenticated_redirected_from_dashboard(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302
    assert "/user/login/" in response["Location"]


@pytest.mark.django_db
def test_hacker_can_view_dashboard(hacker_client):
    client, user = hacker_client
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_hacker_can_submit_application(hacker_client):
    client, user = hacker_client
    resume = SimpleUploadedFile("cv.pdf", b"pdf content", content_type="application/pdf")
    data = {**VALID_HACKER_FORM, "resume": resume}
    response = client.post(reverse("dashboard"), data=data)
    assert response.status_code == 302
    assert HackerApplication.objects.filter(user=user, status=APP_PENDING).exists()


@pytest.mark.django_db
def test_hacker_cannot_submit_duplicate(hacker_client):
    client, user = hacker_client
    HackerApplicationFactory(user=user)
    resume = SimpleUploadedFile("cv.pdf", b"pdf content", content_type="application/pdf")
    data = {**VALID_HACKER_FORM, "resume": resume}
    client.post(reverse("dashboard"), data=data)
    # OneToOneField constraint means there is always exactly one application per user
    assert HackerApplication.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_hacker_can_cancel_invited(hacker_client):
    # APP_PENDING cannot be cancelled — can_be_cancelled() requires INVITED/CONFIRMED/LAST_REMINDER
    client, user = hacker_client
    app = HackerApplicationFactory(user=user, status=APP_INVITED)
    response = client.post(reverse("cancel_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_CANCELLED


@pytest.mark.django_db
def test_invited_hacker_can_confirm(hacker_client):
    # ConfirmApplication is GET-only
    client, user = hacker_client
    app = HackerApplicationFactory(user=user, status=APP_INVITED)
    response = client.get(reverse("confirm_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_CONFIRMED


@pytest.mark.django_db
def test_pending_hacker_cannot_confirm(hacker_client):
    # confirm() raises ValidationError for PENDING status → view raises Http404
    client, user = hacker_client
    app = HackerApplicationFactory(user=user, status=APP_PENDING)
    response = client.get(reverse("confirm_app", kwargs={"id": app.uuid_str}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_organizer_can_vote_on_application(organizer_client, db):
    client, organizer = organizer_client
    app = HackerApplicationFactory()
    response = client.post(
        reverse("review_detail", kwargs={"id": app.uuid_str}),
        data={"app_id": str(app.pk), "tech_rat": "3", "pers_rat": "4"},
    )
    assert response.status_code == 302
    assert Vote.objects.filter(application=app, user=organizer).count() == 1
