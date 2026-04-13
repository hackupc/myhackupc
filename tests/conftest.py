import pytest

from tests.factories import (
    DirectorUserFactory,
    MentorUserFactory,
    OrganizerUserFactory,
    SponsorUserFactory,
    UserFactory,
    VolunteerUserFactory,
)


@pytest.fixture(autouse=True)
def use_locmem_email_backend(settings):
    """Override email backend so confirm views don't attempt to hit SendGrid."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


@pytest.fixture
def hacker_user(db):
    return UserFactory()


@pytest.fixture
def organizer_user(db):
    return OrganizerUserFactory()


@pytest.fixture
def volunteer_user(db):
    return VolunteerUserFactory()


@pytest.fixture
def mentor_user(db):
    return MentorUserFactory()


@pytest.fixture
def sponsor_user(db):
    return SponsorUserFactory()


@pytest.fixture
def hacker_client(client, hacker_user):
    client.force_login(hacker_user)
    return client, hacker_user


@pytest.fixture
def organizer_client(client, organizer_user):
    client.force_login(organizer_user)
    return client, organizer_user


@pytest.fixture
def volunteer_client(client, volunteer_user):
    client.force_login(volunteer_user)
    return client, volunteer_user


@pytest.fixture
def mentor_client(client, mentor_user):
    client.force_login(mentor_user)
    return client, mentor_user


@pytest.fixture
def sponsor_client(client, sponsor_user):
    client.force_login(sponsor_user)
    return client, sponsor_user


@pytest.fixture
def director_user(db):
    return DirectorUserFactory()


@pytest.fixture
def director_client(client, director_user):
    client.force_login(director_user)
    return client, director_user
