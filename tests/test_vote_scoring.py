from importlib import import_module
from math import sqrt
from types import SimpleNamespace

import pytest
from django.db import connection
from django.db.migrations.loader import MigrationLoader

from organizers.models import Vote
from tests.factories import HackerApplicationFactory, OrganizerUserFactory


pytestmark = pytest.mark.django_db


def cast_votes(user, marks):
    return [Vote.objects.create(application=HackerApplicationFactory(), user=user,
                                tech=tech, personal=personal)
            for tech, personal in marks]


@pytest.mark.parametrize('marks, expected', [
    ([(3, 3), (4, 4)], [-0.5, 0.5]),
    ([(1, 1), (5, 5)], [-0.5, 0.5]),
    ([(1, 4), (5, 2)], [0.3, -0.3]),
    ([(1, 1), (2, 2), (2, 2)], [-sqrt(2) / 2, sqrt(2) / 4, sqrt(2) / 4]),
    ([(3, 3)], [0]),
    ([(3, 3), (3, 3)], [0, 0]),
    ([(3, 2), (3, 4)], [-0.4, 0.4]),
])
def test_normalized_scores(marks, expected, organizer_user):
    votes = cast_votes(organizer_user, marks)
    for vote, score in zip(votes, expected):
        vote.refresh_from_db()
        assert vote.calculated_vote == pytest.approx(score)
    assert [(v.tech, v.personal) for v in votes] == marks


def test_recalculation_preserves_skips_and_other_reviewers(organizer_user):
    other = cast_votes(OrganizerUserFactory(), [(1, 1), (5, 5)])
    first, skip = cast_votes(organizer_user, [(3, 3), (None, None)])
    cast_votes(organizer_user, [(4, 4)])
    first.refresh_from_db()
    skip.refresh_from_db()
    assert first.calculated_vote == pytest.approx(-0.5)
    assert skip.calculated_vote is None
    for vote, expected in zip(other, [-0.5, 0.5]):
        vote.refresh_from_db()
        assert vote.calculated_vote == pytest.approx(expected)


def test_migration_recalculates_existing_scores(organizer_user):
    first, second, skip = cast_votes(organizer_user, [(3, 3), (4, 4), (None, None)])
    Vote.objects.filter(pk=first.pk).update(calculated_vote=-1)
    Vote.objects.filter(pk=second.pk).update(calculated_vote=1)
    orphan = Vote.objects.create(application=HackerApplicationFactory(), calculated_vote=0.7)
    Vote.objects.filter(pk=orphan.pk).update(tech=4, personal=4)
    cast_votes(OrganizerUserFactory(), [(None, None)])

    migration = import_module('organizers.migrations.0006_correct_vote_standard_deviation')
    historical_apps = MigrationLoader(connection).project_state(
        [('organizers', '0006_correct_vote_standard_deviation')]).apps
    migration.recalculate_votes(historical_apps, SimpleNamespace(connection=connection))

    for vote, expected in [(first, -0.5), (second, 0.5), (orphan, 0.7)]:
        vote.refresh_from_db()
        assert vote.calculated_vote == pytest.approx(expected)
    skip.refresh_from_db()
    assert skip.calculated_vote is None
    assert (first.tech, first.personal, second.tech, second.personal) == (3, 3, 4, 4)
