from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from applications.models import APP_CONFIRMED, APP_DUBIOUS, APP_INVITED, APP_PENDING, APP_REJECTED
from organizers.models import ApplicationComment, Vote
from tests.factories import (
    HackerApplicationFactory,
    MentorApplicationFactory,
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
