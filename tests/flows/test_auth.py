import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from tests.factories import UserFactory
from user.tokens import account_activation_token, password_reset_token

User = get_user_model()

VALID_SIGNUP_FORM = {
    "name": "Gerard Madrid",
    "email": "newuser@example.com",
    "password": "S3curePass!x",
    "password2": "S3curePass!x",
    "terms_and_conditions": True,
}


@pytest.mark.django_db
def test_signup_creates_user_and_logs_in(client):
    response = client.post(reverse("account_signup"), data=VALID_SIGNUP_FORM)

    assert response.status_code == 302
    assert User.objects.filter(email="newuser@example.com").count() == 1
    assert response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_signup_rejects_duplicate_email(client):
    UserFactory(email="newuser@example.com")

    response = client.post(reverse("account_signup"), data=VALID_SIGNUP_FORM)

    assert response.status_code == 200
    assert User.objects.filter(email="newuser@example.com").count() == 1


@pytest.mark.django_db
def test_signup_rejects_mismatched_passwords(client):
    response = client.post(reverse("account_signup"), data={**VALID_SIGNUP_FORM, "password2": "Different1!"})

    assert response.status_code == 200
    assert User.objects.filter(email="newuser@example.com").count() == 0


@pytest.mark.django_db
def test_login_with_valid_credentials(client):
    UserFactory(email="hacker@example.com")

    response = client.post(reverse("account_login"), data={"email": "hacker@example.com", "password": "testpass123"})

    assert response.status_code == 302
    assert response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_login_with_wrong_password_shows_error(client):
    UserFactory(email="hacker@example.com")

    response = client.post(reverse("account_login"), data={"email": "hacker@example.com", "password": "wrongpass1!"})

    assert response.status_code == 200
    assert b"Incorrect username or password" in response.content


@pytest.mark.django_db
def test_login_succeeds_after_failed_attempt(client):
    UserFactory(email="hacker@example.com")
    client.post(reverse("account_login"), data={"email": "hacker@example.com", "password": "wrongpass1!"})

    response = client.post(reverse("account_login"), data={"email": "hacker@example.com", "password": "testpass123"})

    assert response.status_code == 302
    assert response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_logout_deauthenticates(hacker_client):
    client, user = hacker_client

    response = client.get(reverse("account_logout"))

    assert response.status_code == 302
    assert not response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_password_reset_sends_email(client):
    UserFactory(email="hacker@example.com")

    response = client.post(reverse("password_reset"), data={"email": "hacker@example.com"})

    assert response.status_code == 302
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_password_reset_rejects_unknown_email(client):
    response = client.post(reverse("password_reset"), data={"email": "nobody@example.com"})

    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_sets_new_password(client):
    user = UserFactory(email="hacker@example.com")
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token.make_token(user)

    response = client.post(
        reverse("password_reset_confirm", kwargs={"uid": uid, "token": token}),
        data={"new_password1": "Fr3shPass!x", "new_password2": "Fr3shPass!x"},
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.check_password("Fr3shPass!x")


@pytest.mark.django_db
def test_password_reset_confirm_rejects_invalid_token(client):
    user = UserFactory(email="hacker@example.com")
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = client.get(reverse("password_reset_confirm", kwargs={"uid": uid, "token": "123-abc"}))

    assert response.status_code == 200
    assert response.context["validlink"] is False


@pytest.mark.django_db
def test_activate_verifies_email(client):
    user = UserFactory(email="hacker@example.com", email_verified=False)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    response = client.get(reverse("activate", kwargs={"uid": uid, "token": token}))

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.email_verified


@pytest.mark.django_db
def test_activate_with_unknown_user_redirects(client):
    uid = urlsafe_base64_encode(force_bytes(99999))

    response = client.get(reverse("activate", kwargs={"uid": uid, "token": "123-abc"}))

    assert response.status_code == 302


@pytest.mark.django_db
def test_send_email_verification_for_unverified_user(client):
    user = UserFactory(email="hacker@example.com", email_verified=False)
    client.force_login(user)
    mail.outbox.clear()

    response = client.get(reverse("send_email_verification"))

    assert response.status_code == 302
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_verify_email_required_redirects_verified_user(hacker_client):
    client, user = hacker_client

    response = client.get(reverse("verify_email_required"))

    assert response.status_code == 302
