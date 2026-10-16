from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from math import ceil
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import close_old_connections, connection
from django.urls import reverse
from django.utils import timezone

from applications.models import APP_CANCELLED, APP_CONFIRMED, APP_INVITED, APP_PENDING, APP_REJECTED, AcceptedResume
from organizers.models import Vote
from organizers.review_policy import add_vote, rank_urgencies, review_cutoff_rank, reviewable_applications
from tests.factories import HackerApplicationFactory, OrganizerUserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def policy_settings(settings):
    settings.MIN_VOTES_TO_APP = 5
    settings.MAX_VOTES_TO_APP = 12
    settings.N_MAX_LIVE_HACKERS = 2
    settings.HACKER_INVITE_EXTRA_PERCENT = 0
    settings.REVIEW_EARLY_CUTOFF_PERCENT = 100
    settings.REVIEW_RANDOM_POOL_SIZE = 25
    settings.REVIEW_FULL_URGENCY_PERCENT = 0
    settings.REVIEW_ZERO_URGENCY_PERCENT = 1
    settings.REVIEW_DISPUTE_GAP = 1.0


@pytest.fixture
def scored_app():
    reviewers = OrganizerUserFactory.create_batch(12)

    def create(scores=(), **kwargs):
        kwargs.setdefault('submission_date', timezone.now() - timedelta(hours=3))
        app = HackerApplicationFactory(**kwargs)
        # Fixed normalized scores isolate queue rules from reviewer calibration.
        Vote.objects.bulk_create([
            Vote(application=app, user=user, calculated_vote=score,
                 tech=3 if score is not None else None, personal=3 if score is not None else None)
            for user, score in zip(reviewers, scores)
        ])
        return app

    return create


def test_baseline_borderline_disagreement_and_cap(scored_app, organizer_user):
    strong = scored_app([1] * 5)
    borderline = scored_app([0.2] * 5)
    weak = scored_app([-1] * 5)
    disputed = scored_app([-1, -1, -1, -1, 1])
    capped = scored_app([-1, 1] * 6)
    new = scored_app([-1] * 4)

    queue = list(reviewable_applications(organizer_user))

    assert queue[0] == new
    assert set(queue) == {new, borderline, disputed}
    assert strong not in queue and weak not in queue and capped not in queue


def test_early_cutoff_uses_only_applicants_with_baseline_reviews(scored_app, organizer_user, settings):
    settings.REVIEW_EARLY_CUTOFF_PERCENT = 50
    paused = scored_app([0.2] * 5)
    unfinished = scored_app([1] * 4)
    assert list(reviewable_applications(organizer_user)) == [unfinished, paused]

    # A newly ranked stronger applicant moves the early midpoint.
    stronger = scored_app([1] * 5)
    assert list(reviewable_applications(organizer_user)) == [unfinished, stronger]


@pytest.mark.parametrize('pool, expected', [
    (0, 0), (100, 50), (400, 200), (875, 438),
    (1000, 500), (1500, 750), (1750, 875), (2000, 875),
])
def test_cutoff_grows_to_invitation_target(pool, expected, settings):
    settings.N_MAX_LIVE_HACKERS = 700
    settings.HACKER_INVITE_EXTRA_PERCENT = 25
    settings.REVIEW_EARLY_CUTOFF_PERCENT = 50
    assert review_cutoff_rank(pool) == expected


@pytest.mark.parametrize('percent', [0, -1, 101])
def test_invalid_early_cutoff_fails_clearly(percent, settings):
    settings.REVIEW_EARLY_CUTOFF_PERCENT = percent
    with pytest.raises(ImproperlyConfigured):
        review_cutoff_rank(100)


def test_unanimously_below_cutoff_stops_even_with_a_large_spread(scored_app, organizer_user, settings):
    settings.N_MAX_LIVE_HACKERS = 1
    boundary = scored_app([0] * 5)
    scored_app([-3, -3, -3, -3, -1])
    assert set(reviewable_applications(organizer_user)) == {boundary}


def test_cutoff_moves_and_reopens_applications(scored_app, organizer_user):
    top = scored_app([1] * 5)
    old_boundary = scored_app([0.5] * 5)
    paused = scored_app([0] * 5)
    assert set(reviewable_applications(organizer_user)) == {old_boundary}

    # Scores can change when an organizer reviews other applications.
    Vote.objects.filter(application=top).update(calculated_vote=-1)
    assert set(reviewable_applications(organizer_user)) == {paused}


def test_waitlisted_and_confirmed_applicants_remain_in_ranking(scored_app, organizer_user, settings):
    settings.REVIEW_FULL_URGENCY_PERCENT = 34
    settings.REVIEW_ZERO_URGENCY_PERCENT = 40
    scored_app([2] * 5, status=APP_CONFIRMED)
    scored_app([1] * 5, status=APP_REJECTED)
    near = scored_app([0.9] * 5)
    scored_app([0] * 5)
    assert set(reviewable_applications(organizer_user)) == {near}


def test_invitation_buffer_moves_cutoff(scored_app, organizer_user, settings):
    settings.N_MAX_LIVE_HACKERS = 4
    settings.HACKER_INVITE_EXTRA_PERCENT = 25
    apps = [scored_app([score] * 5) for score in [5, 4, 3, 2, 1, 0]]
    assert set(reviewable_applications(organizer_user)) == {apps[4]}
    apps[0].status = APP_CONFIRMED
    apps[0].save()
    # Confirmed hackers remain ranked, so the boundary stays at absolute rank five.
    assert set(reviewable_applications(organizer_user)) == {apps[4]}
    apps[0].status = APP_CANCELLED
    apps[0].save()
    assert set(reviewable_applications(organizer_user)) == {apps[5]}


def test_weekly_invitations_do_not_shift_early_cutoff(scored_app, organizer_user, settings):
    settings.N_MAX_LIVE_HACKERS = 20
    settings.REVIEW_EARLY_CUTOFF_PERCENT = 50
    apps = [scored_app([score] * 5) for score in [6, 5, 4, 3, 2, 1]]
    before = list(reviewable_applications(organizer_user))
    assert before == [apps[2]]
    apps[0].status = APP_INVITED
    apps[0].save()
    apps[1].status = APP_CONFIRMED
    apps[1].save()
    assert list(reviewable_applications(organizer_user)) == before


def test_rank_bands_and_review_targets_for_2000_applicants(settings):
    settings.REVIEW_FULL_URGENCY_PERCENT = 5
    settings.REVIEW_ZERO_URGENCY_PERCENT = 15
    ranked = [(rank, -rank) for rank in range(1, 2001)]
    groups = rank_urgencies(ranked, 875)
    urgencies = {pk: urgency for urgency, ids in groups.items() for pk in ids}
    for rank, urgency, target in [(575, 0, 5), (625, .25, 7), (675, .5, 9),
                                  (725, .75, 11), (775, 1, 12), (875, 1, 12),
                                  (975, 1, 12), (1025, .75, 11), (1075, .5, 9),
                                  (1125, .25, 7), (1175, 0, 5)]:
        actual = urgencies.get(rank, 0)
        assert actual == pytest.approx(urgency)
        assert ceil(5 + 7 * actual) == target


def test_equal_scores_are_not_split_by_application_id(settings):
    settings.REVIEW_FULL_URGENCY_PERCENT = 0
    settings.REVIEW_ZERO_URGENCY_PERCENT = 10
    ranked = [(1, 2), (2, 1), (3, 1), (4, 1), (5, 0)]
    assert rank_urgencies(ranked, 3) == {1.0: [2, 3, 4]}


@pytest.mark.parametrize('full, zero', [(-1, 15), (15, 5), (5, 5), (5, 101)])
def test_invalid_bands_fail_clearly(full, zero, settings):
    settings.REVIEW_FULL_URGENCY_PERCENT = full
    settings.REVIEW_ZERO_URGENCY_PERCENT = zero
    with pytest.raises(ImproperlyConfigured):
        rank_urgencies([(1, 0)], 1)


def test_urgency_orders_extra_reviews_and_limits_their_number(scored_app, organizer_user, settings):
    settings.N_MAX_LIVE_HACKERS = 5
    settings.REVIEW_FULL_URGENCY_PERCENT = 10
    settings.REVIEW_ZERO_URGENCY_PERCENT = 30
    apps = [scored_app([score] * 5) for score in range(10, 0, -1)]
    baseline = scored_app([0] * 4)
    queue = list(reviewable_applications(organizer_user))
    # Rank 5 is the cutoff. Ranks 4-6 get 100%; ranks 3 and 7 get 50%.
    assert queue == [baseline, apps[3], apps[4], apps[5], apps[2], apps[6]]
    assert [(app.review_urgency, app.review_target) for app in queue[1:]] == [
        (1, 12), (1, 12), (1, 12), (.5, 9), (.5, 9),
    ]
    Vote.objects.bulk_create([
        Vote(application=apps[2], user=OrganizerUserFactory(), tech=3, personal=3, calculated_vote=8)
        for _ in range(4)
    ])
    assert apps[2] not in reviewable_applications(organizer_user)


def test_online_applications_do_not_move_in_person_cutoff(scored_app, organizer_user):
    scored_app(status=APP_CONFIRMED, online=True)
    scored_app([2] * 5, online=True)
    scored_app([1] * 5)
    boundary = scored_app([0] * 5)
    assert set(reviewable_applications(organizer_user)) == {boundary}


def test_full_capacity_still_allows_baseline_and_disagreement(scored_app, organizer_user, settings):
    settings.N_MAX_LIVE_HACKERS = 0
    scored_app([0] * 5)
    new = scored_app()
    disputed = scored_app([-1, 1] * 3)
    assert set(reviewable_applications(organizer_user)) == {new, disputed}


@pytest.mark.parametrize('reason', ['cap', 'clear', 'young', 'own', 'voted', 'skipped', 'status'])
def test_queue_counter_direct_link_and_post_agree(reason, scored_app, organizer_client, settings):
    client, user = organizer_client
    kwargs = {'user': user} if reason == 'own' else {}
    app = scored_app([0] * 12 if reason == 'cap' else [0] * 5 if reason == 'clear' else [], **kwargs)
    if reason == 'clear':
        # Keep the tested application well below a real boundary.
        settings.N_MAX_LIVE_HACKERS = 1
        scored_app([1] * 5, status=APP_REJECTED)
    if reason == 'young':
        app.submission_date = timezone.now()
    elif reason == 'status':
        app.status = APP_REJECTED
    elif reason in ['voted', 'skipped']:
        Vote.objects.create(application=app, user=user, tech=3 if reason == 'voted' else None,
                            personal=3 if reason == 'voted' else None)
    app.save()
    before = app.vote_set.count()

    response = client.get(reverse('review'))
    assert response.context['app'] is None
    assert response.context['apps_left_to_vote'] == 0
    assert response.context['tabs'][1][2] == ''
    detail_url = reverse('review_detail', kwargs={'id': app.uuid_str})
    response = client.get(detail_url)
    assert response.status_code == 302
    assert response.url == reverse('app_detail', kwargs={'id': app.uuid_str})

    for url in [reverse('review'), detail_url]:
        response = client.post(url, {'app_id': app.pk, 'tech_rat': '3', 'pers_rat': '4'})
        assert response.status_code == 302
    assert app.vote_set.count() == before


def test_counter_counts_only_current_review_work(scored_app, organizer_client):
    client, user = organizer_client
    scored_app([1] * 5)
    boundary = scored_app([0] * 5)
    new = scored_app()
    scored_app([-1] * 5)
    response = client.get(reverse('review'))
    assert response.context['app'] == new
    assert response.context['apps_left_to_vote'] == 2
    assert response.context['tabs'][1][2] == 'new'
    response = client.get(reverse('review_detail', kwargs={'id': boundary.uuid_str}))
    assert response.context['app'] == boundary


@pytest.mark.parametrize('pool_size, expected_size', [(2, 2), (25, 3)])
def test_next_application_mixes_only_leading_highest_priority(
        pool_size, expected_size, scored_app, organizer_client, settings):
    settings.REVIEW_RANDOM_POOL_SIZE = pool_size
    client, user = organizer_client
    baseline = [scored_app() for _ in range(3)]
    scored_app([0] * 5)
    with patch('organizers.review_policy.choice', side_effect=lambda apps: apps[-1]) as choose:
        response = client.get(reverse('review'))
    candidates = choose.call_args.args[0]
    assert candidates == baseline[:expected_size]
    assert response.context['app'] == baseline[expected_size - 1]


def test_next_request_uses_new_votes(scored_app, organizer_client):
    client, user = organizer_client
    app = scored_app([0] * 11)
    assert client.get(reverse('review')).context['app'] == app
    add_vote(app, OrganizerUserFactory(), 3, 3)
    assert client.get(reverse('review')).context['app'] is None


def test_skips_do_not_finish_baseline_or_approve_cv(scored_app, organizer_user):
    app = scored_app([0] * 4)
    add_vote(app, organizer_user, None, None)
    assert app.scored_vote_count == 4
    assert not AcceptedResume.objects.filter(application=app).exists()
    assert app not in reviewable_applications(organizer_user)
    other = OrganizerUserFactory()
    assert app in reviewable_applications(other)
    add_vote(app, other, 3, 3)
    assert AcceptedResume.objects.filter(application=app, accepted=True).exists()


@pytest.mark.parametrize('marks', [('0', '3'), ('6', '3'), ('bad', '3'), ('3', ''), ('3', None), (None, None)])
def test_invalid_scores_do_not_create_votes(marks, scored_app, organizer_client):
    client, user = organizer_client
    app = scored_app()
    data = {'app_id': app.pk}
    data.update({key: value for key, value in zip(['tech_rat', 'pers_rat'], marks) if value is not None})
    assert client.post(reverse('review'), data).status_code == 302
    assert not app.vote_set.exists()


def test_direct_link_missing_or_mismatched_application(scored_app, organizer_client):
    client, user = organizer_client
    app, other = scored_app(), scored_app()
    missing = reverse('review_detail', kwargs={'id': '00000000000000000000000000000000'})
    assert client.get(missing).status_code == 404
    response = client.post(reverse('review_detail', kwargs={'id': app.uuid_str}),
                           {'app_id': other.pk, 'tech_rat': '3', 'pers_rat': '3'})
    assert response.status_code == 404
    assert not other.vote_set.exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_votes_cannot_exceed_cap(scored_app, settings):
    name = str(connection.settings_dict['NAME'])
    if connection.vendor == 'sqlite' and (name == ':memory:' or 'mode=memory' in name):
        pytest.skip('Concurrent writers need file-backed SQLite or PostgreSQL.')
    settings.N_MAX_LIVE_HACKERS = 1
    app = scored_app([0] * 11)
    reviewers = OrganizerUserFactory.create_batch(2)
    start = Barrier(2)

    def submit(user):
        close_old_connections()
        try:
            start.wait(timeout=5)
            try:
                add_vote(app, user, 3, 3)
                return True
            except ValidationError:
                return False
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, reviewers))
    assert sorted(results) == [False, True]
    assert app.vote_set.filter(calculated_vote__isnull=False).count() == 12
    app.refresh_from_db()
    assert app.status == APP_PENDING
