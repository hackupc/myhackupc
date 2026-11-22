from datetime import timedelta

import pytest
from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from applications.models import (
    APP_CONFIRMED,
    APP_DISCARDED,
    APP_DUBIOUS,
    APP_INVITED,
    APP_PENDING,
    APP_REJECTED,
)
from organizers.models import ApplicationComment, ApplicationDiscard, Vote
from organizers.views.application_lists import hacker_tabs
from tests.factories import (
    HackerApplicationFactory,
    MentorApplicationFactory,
    OrganizerUserFactory,
    SponsorApplicationFactory,
    VolunteerApplicationFactory,
    VolunteerUserFactory,
)
from organizers.views.review import add_comment


@pytest.mark.django_db
def test_not_dubious_with_volunteer_user_role(director_client):
    client, director = director_client
    app = HackerApplicationFactory(user=VolunteerUserFactory())
    app.set_dubious(director, "Other", "Needs review")

    response = client.post(
        reverse("app_detail", kwargs={"id": app.uuid_str}),
        data={"app_id": str(app.pk), "unset_dubious": "true"},
    )

    assert response.status_code == 302
    app.refresh_from_db()
    assert app.status == APP_PENDING
    assert app.dubioused_by is None
    comment = ApplicationComment.objects.get(hacker=app)
    assert comment.author == director
    assert comment.volunteer_id is None
    assert "No problems, hacker allowed to participate" in comment.text


@pytest.mark.django_db
@pytest.mark.parametrize("factory, field", [
    (HackerApplicationFactory, "hacker"),
    (VolunteerApplicationFactory, "volunteer"),
    (MentorApplicationFactory, "mentor"),
    (SponsorApplicationFactory, "sponsor"),
])
def test_comments_follow_application_type_after_user_role_change(organizer_user, factory, field):
    app = factory(user=organizer_user)

    comment = add_comment(app, organizer_user, "Reviewed")

    comment.refresh_from_db()
    assert comment.application == app
    for application_field in ("hacker", "volunteer", "mentor", "sponsor"):
        assert getattr(comment, application_field + "_id") == (app.pk if application_field == field else None)


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
def test_review_counts_votes_once_when_app_has_discard_records(organizer_client):
    client, _ = organizer_client
    now = timezone.now()
    fewer_votes = HackerApplicationFactory(
        submission_date=now - timedelta(hours=3) + timedelta(minutes=1)
    )
    more_votes = HackerApplicationFactory(
        submission_date=now - timedelta(hours=3)
    )

    for _ in range(2):
        Vote.objects.create(
            application=fewer_votes,
            user=OrganizerUserFactory(),
            tech=None,
            personal=None,
            calculated_vote=1.0,
        )
    for _ in range(4):
        Vote.objects.create(
            application=more_votes,
            user=OrganizerUserFactory(),
            tech=None,
            personal=None,
            calculated_vote=1.0,
        )
    for _ in range(4):
        ApplicationDiscard.objects.create(
            application=fewer_votes, user=OrganizerUserFactory()
        )

    response = client.get(reverse("review"))

    assert response.context["app"].pk == fewer_votes.pk
    assert response.context["apps_left_to_vote"] == 2


@pytest.mark.django_db
def test_review_tab_badge_ignores_app_discarded_by_reviewer(organizer_client):
    _, reviewer = organizer_client
    app = reviewable_application()
    ApplicationDiscard.objects.create(application=app, user=reviewer)

    tabs = hacker_tabs(reviewer)

    assert tabs[1][2] == ""


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
    client, user = hx_client
    app = HackerApplicationFactory(
        status=APP_DUBIOUS,
        resume=SimpleUploadedFile("old.pdf", b"%PDF-1.4 old", content_type="application/pdf"),
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
    assert ApplicationComment.objects.filter(
        hacker=app, author=user, text="Resume updated"
    ).exists()


@pytest.mark.django_db
def test_organizer_without_hx_cannot_change_hacker_resume(organizer_client):
    client, _ = organizer_client
    app = HackerApplicationFactory(status=APP_DUBIOUS, resume=_pdf_file("old.pdf"))

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
    app = HackerApplicationFactory(status=APP_DUBIOUS, resume=_pdf_file("old.pdf"))

    response = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))

    assert response.status_code == 200
    assert b"Change CV" in response.content


@pytest.mark.django_db
def test_hx_cannot_change_resume_when_application_is_not_dubious(hx_client):
    client, _ = hx_client
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
    detail = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))
    assert b"Change CV" not in detail.content


@pytest.mark.django_db
def test_hx_does_not_see_change_cv_button_during_review(hx_client):
    client, _ = hx_client
    app = reviewable_application(resume=_pdf_file("old.pdf"))

    response = client.get(reverse("review"))

    assert response.status_code == 200
    assert response.context["app"].pk == app.pk
    assert b"Change CV" not in response.content


@pytest.mark.django_db
def test_organizer_without_hx_does_not_see_change_cv_button(organizer_client):
    client, _ = organizer_client
    app = HackerApplicationFactory(status=APP_DUBIOUS, resume=_pdf_file("old.pdf"))

    response = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))

    assert response.status_code == 200
    assert b"Change CV" not in response.content


@pytest.fixture
def dubious_reviewer_client(client, db):
    reviewer = OrganizerUserFactory(can_review_dubious=True)
    client.force_login(reviewer)
    return client, reviewer


@pytest.mark.django_db
def test_dubious_reviewer_can_change_resume_when_application_is_dubious(dubious_reviewer_client):
    client, user = dubious_reviewer_client
    app = HackerApplicationFactory(
        status=APP_DUBIOUS,
        resume=SimpleUploadedFile("old.pdf", b"%PDF-1.4 old", content_type="application/pdf"),
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
    assert ApplicationComment.objects.filter(
        hacker=app, author=user, text="Resume updated"
    ).exists()


@pytest.mark.django_db
def test_dubious_reviewer_cannot_change_resume_when_application_is_not_dubious(dubious_reviewer_client):
    client, _ = dubious_reviewer_client
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
def test_dubious_reviewer_sees_change_cv_only_on_dubious_applications(dubious_reviewer_client):
    client, _ = dubious_reviewer_client
    dubious_app = HackerApplicationFactory(status=APP_DUBIOUS, resume=_pdf_file("dubious.pdf"))
    pending_app = HackerApplicationFactory(resume=_pdf_file("pending.pdf"))

    dubious_response = client.get(reverse("app_detail", kwargs={"id": dubious_app.uuid_str}))
    pending_response = client.get(reverse("app_detail", kwargs={"id": pending_app.uuid_str}))

    assert dubious_response.status_code == 200
    assert b"Change CV" in dubious_response.content
    assert pending_response.status_code == 200
    assert b"Change CV" not in pending_response.content


@pytest.mark.django_db
def test_organizer_without_dubious_access_cannot_change_dubious_resume(organizer_client):
    client, _ = organizer_client
    app = HackerApplicationFactory(status=APP_DUBIOUS, resume=_pdf_file("old.pdf"))

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
    detail = client.get(reverse("app_detail", kwargs={"id": app.uuid_str}))
    assert b"Change CV" not in detail.content


@pytest.mark.django_db
def test_review_shows_discard_button(organizer_client):
    client, _ = organizer_client
    reviewable_application()

    response = client.get(reverse("review"))

    assert response.status_code == 200
    assert b"Mark as possible discard" in response.content


@pytest.mark.django_db
def test_discard_hides_application_from_that_reviewer_only(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()
    other = OrganizerUserFactory()

    response = client.post(reverse("review"), data={"app_id": str(app.pk), "discard": "discard"})

    app.refresh_from_db()
    assert response.status_code == 302
    assert app.status == APP_PENDING
    assert ApplicationDiscard.objects.filter(application=app, user=organizer).count() == 1
    again = client.get(reverse("review"))
    assert again.context["app"] is None

    client.force_login(other)
    other_view = client.get(reverse("review"))
    assert other_view.context["app"].pk == app.pk


@pytest.mark.django_db
def test_required_discards_mark_application_discarded(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()
    reviewers = [organizer] + [
        OrganizerUserFactory() for _ in range(settings.DISCARDS_REQUIRED - 1)
    ]

    for reviewer in reviewers:
        client.force_login(reviewer)
        response = client.post(
            reverse("review"), data={"app_id": str(app.pk), "discard": "discard"}
        )
        assert response.status_code == 302

    app.refresh_from_db()
    assert app.status == APP_DISCARDED
    assert ApplicationDiscard.objects.filter(application=app).count() == settings.DISCARDS_REQUIRED
    assert ApplicationComment.objects.filter(hacker=app, text="Application discarded").count() == 1

    client.force_login(OrganizerUserFactory())
    response = client.get(reverse("review"))
    assert response.context["app"] is None


@pytest.mark.django_db
def test_same_reviewer_cannot_discard_twice(organizer_client):
    client, organizer = organizer_client
    app = reviewable_application()

    client.post(reverse("review"), data={"app_id": str(app.pk), "discard": "discard"})
    client.post(reverse("review"), data={"app_id": str(app.pk), "discard": "discard"})

    assert ApplicationDiscard.objects.filter(application=app, user=organizer).count() == 1
