from datetime import timedelta

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from applications.models import APP_CONFIRMED, APP_DUBIOUS, APP_INVITED, APP_REJECTED
from organizers.models import ApplicationComment, Vote
from tests.factories import HackerApplicationFactory


def reviewable_application(**kwargs):
    return HackerApplicationFactory(submission_date=timezone.now() - timedelta(hours=3), **kwargs)


@pytest.fixture
def director_client(client, director_user):
    client.force_login(director_user)
    return client, director_user


@pytest.mark.django_db
def test_review_shows_oldest_pending_application(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()

    response = client.get(reverse("review"))

    assert response.status_code == 200
    assert response.context["app"].pk == app.pk


@pytest.mark.django_db
def test_review_shows_nothing_when_all_voted(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()
    Vote.objects.create(application=app, user=organizer)

    response = client.get(reverse("review"))

    assert response.status_code == 200
    assert response.context["app"] is None


@pytest.mark.django_db
def test_organizer_can_skip_application(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()

    response = client.post(reverse("review"), data={"app_id": str(app.pk), "skip": "true"})

    assert response.status_code == 302
    assert Vote.objects.filter(application=app, user=organizer, tech=None, personal=None).count() == 1


@pytest.mark.django_db
def test_organizer_can_comment_from_review(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()

    response = client.post(
        reverse("review"), data={"app_id": str(app.pk), "add_comment": "true", "comment_text": "Solid application"}
    )

    assert response.status_code == 302
    assert ApplicationComment.objects.filter(hacker=app, author=organizer, text="Solid application").count() == 1


@pytest.mark.django_db
def test_organizer_can_mark_application_dubious(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()

    response = client.post(
        reverse("review"),
        data={
            "app_id": str(app.pk),
            "set_dubious": "true",
            "dubious_type": "Other",
            "dubious_comment_text": "Suspicious description",
        },
    )

    app.refresh_from_db()
    assert response.status_code == 302
    assert app.status == APP_DUBIOUS


@pytest.mark.django_db
def test_organizer_can_view_application_detail(organizer_client):
    client, organizer = organizer_client
    app = HackerApplicationFactory()

    response = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))

    assert response.status_code == 200
    assert response.context["app"].pk == app.pk


@pytest.mark.django_db
def test_application_detail_unknown_id_returns_404(organizer_client):
    client, organizer = organizer_client

    response = client.get(reverse("app_detail", kwargs={"id": "00000000000000000000000000000000"}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_director_can_invite_application(director_client):
    client, director = director_client
    app = HackerApplicationFactory()

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}), data={"app_id": str(app.pk), "invite": "true"}
    )

    app.refresh_from_db()
    assert response.status_code == 302
    assert app.status == APP_INVITED
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_director_can_confirm_invited_application(director_client):
    client, director = director_client
    app = HackerApplicationFactory(status=APP_INVITED)

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}), data={"app_id": str(app.pk), "confirm": "true"}
    )

    app.refresh_from_db()
    assert response.status_code == 302
    assert app.status == APP_CONFIRMED


@pytest.mark.django_db
def test_director_can_waitlist_pending_application(director_client):
    client, director = director_client
    app = HackerApplicationFactory()

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}), data={"app_id": str(app.pk), "waitlist": "true"}
    )

    app.refresh_from_db()
    assert response.status_code == 302
    assert app.status == APP_REJECTED


@pytest.mark.django_db
def test_organizer_can_comment_on_application_detail(organizer_client):
    client, organizer = organizer_client
    app = HackerApplicationFactory()

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}),
        data={"app_id": str(app.pk), "add_comment": "true", "comment_text": "Reviewed manually"},
    )

    assert response.status_code == 302
    assert ApplicationComment.objects.filter(hacker=app, author=organizer, text="Reviewed manually").count() == 1


def _pdf_file(name="cv.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 content", content_type="application/pdf")


@pytest.mark.django_db
def test_hx_can_change_hacker_resume(hx_client):
    client, _ = hx_client
    app = HackerApplicationFactory(
        resume=SimpleUploadedFile("old.pdf", b"%PDF-1.4 old", content_type="application/pdf")
    )

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}),
        data={
            "app_id": str(app.pk),
            "change_resume": "change_resume",
            "resume": SimpleUploadedFile("new.pdf", b"%PDF-1.4 replaced", content_type="application/pdf"),
        },
    )

    app.refresh_from_db()
    app.resume.open("rb")
    try:
        content = app.resume.read()
    finally:
        app.resume.close()
    assert response.status_code == 302
    assert b"replaced" in content


@pytest.mark.django_db
def test_organizer_without_hx_cannot_change_hacker_resume(organizer_client):
    client, _ = organizer_client
    app = HackerApplicationFactory(resume=_pdf_file("old.pdf"))

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}),
        data={
            "app_id": str(app.pk),
            "change_resume": "change_resume",
            "resume": SimpleUploadedFile("new.pdf", b"%PDF-1.4 replaced", content_type="application/pdf"),
        },
    )

    app.refresh_from_db()
    app.resume.open("rb")
    try:
        content = app.resume.read()
    finally:
        app.resume.close()
    assert response.status_code == 302
    assert b"replaced" not in content


@pytest.mark.django_db
def test_hx_sees_change_cv_button(hx_client):
    client, _ = hx_client
    app = HackerApplicationFactory(resume=_pdf_file("old.pdf"))

    response = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))

    assert response.status_code == 200
    assert b"Change CV" in response.content


@pytest.mark.django_db
def test_organizer_without_hx_does_not_see_change_cv_button(organizer_client):
    client, _ = organizer_client
    app = HackerApplicationFactory(resume=_pdf_file("old.pdf"))

    response = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))

    assert response.status_code == 200
    assert b"Change CV" not in response.content
