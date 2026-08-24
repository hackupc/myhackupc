import pytest
from django.contrib.auth import get_user_model

from tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
def test_unaccented_query_matches_accented_name():
    UserFactory(name="Gerard Màdrid")

    result = User.objects.filter(name__unaccent__icontains="madrid")

    assert result.count() == 1


@pytest.mark.django_db
def test_accented_query_matches_unaccented_name():
    UserFactory(name="Gerard Madrid")

    result = User.objects.filter(name__unaccent__icontains="mÀdRíD")

    assert result.count() == 1


@pytest.mark.django_db
def test_non_matching_query_returns_nothing():
    UserFactory(name="Gerard Màdrid")

    result = User.objects.filter(name__unaccent__icontains="mdrid")

    assert result.count() == 0
