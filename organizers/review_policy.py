"""Shared queue rules. Stopping reviews never accepts or rejects an applicant."""
from datetime import timedelta
from itertools import groupby
from math import ceil
from random import choice

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.db.models import Avg, Case, Count, F, FloatField, Max, Min, Q, Value, When
from django.db.models.functions import Ceil
from django.utils import timezone

from applications.models import (
    APP_ATTENDED, APP_CONFIRMED, APP_INVITED, APP_LAST_REMIDER,
    APP_PENDING, APP_REJECTED, AcceptedResume, HackerApplication,
)
from organizers.models import Vote
from user.models import User


def review_cutoff_rank(pool_size):
    """Grow from the configured percentile to the final invitation target."""
    percent = settings.REVIEW_EARLY_CUTOFF_PERCENT
    if not 0 < percent <= 100:
        raise ImproperlyConfigured('REVIEW_EARLY_CUTOFF_PERCENT must be greater than 0 and at most 100.')
    target = ceil(settings.N_MAX_LIVE_HACKERS * (1 + settings.HACKER_INVITE_EXTRA_PERCENT / 100))
    return max(0, min(target, ceil(pool_size * percent / 100)))


def next_review_application(applications):
    """Mix a short leading group without putting lower urgency ahead of higher."""
    size = settings.REVIEW_RANDOM_POOL_SIZE
    if size < 1:
        raise ImproperlyConfigured('REVIEW_RANDOM_POOL_SIZE must be at least 1.')
    candidates = list(applications[:size])
    if not candidates:
        return None
    priority = candidates[0].review_priority
    return choice([app for app in candidates if app.review_priority == priority])


def rank_urgencies(ranked, cutoff_rank):
    """Group applicant IDs by urgency; equal scores always get equal treatment."""
    full = settings.REVIEW_FULL_URGENCY_PERCENT
    zero = settings.REVIEW_ZERO_URGENCY_PERCENT
    if not 0 <= full < zero <= 100:
        raise ImproperlyConfigured('Review bands must satisfy 0 <= full < zero <= 100.')
    if not 1 <= cutoff_rank <= len(ranked):
        return {}
    inner = len(ranked) * full / 100
    outer = len(ranked) * zero / 100
    groups = {}
    start = 1
    for score, rows in groupby(ranked, key=lambda row: row[1]):
        ids = [pk for pk, _ in rows]
        end = start + len(ids) - 1
        # Use the nearest rank in a tie, so ties crossing the cutoff get full urgency.
        distance = max(start - cutoff_rank, cutoff_rank - end, 0)
        urgency = min(1.0, max(0.0, (outer - distance) / (outer - inner)))
        if urgency > 0:
            groups.setdefault(urgency, []).extend(ids)
        start = end + 1
    return groups


def reviewable_applications(user):
    """Baseline reviews first, then urgency; all entry points use this queue."""
    minimum = settings.MIN_VOTES_TO_APP
    maximum = settings.MAX_VOTES_TO_APP
    if not 1 <= minimum <= maximum or settings.HACKER_INVITE_EXTRA_PERCENT < 0:
        raise ImproperlyConfigured('Review limits must satisfy 1 <= min <= max; extra invitations must be >= 0.')
    applications = HackerApplication.objects.annotate(
        review_count=Count('vote__calculated_vote'),
        review_score=Avg('vote__calculated_vote'),
        review_low=Min('vote__calculated_vote'),
        review_high=Max('vote__calculated_vote'),
        review_spread=Max('vote__calculated_vote') - Min('vote__calculated_vote'),
    )

    cutoff = None
    # At our scale (~2,000 applicants), ranking once in Python keeps ties simple.
    # Keep invited/confirmed hackers: weekly batches must not move the boundary.
    ranked = list(applications.filter(
        status__in=[APP_PENDING, APP_REJECTED, APP_INVITED, APP_LAST_REMIDER, APP_CONFIRMED, APP_ATTENDED],
        online=False,
        review_count__gte=minimum,
    ).order_by('-review_score', 'pk').values_list('pk', 'review_score'))
    places = review_cutoff_rank(len(ranked))
    urgencies = rank_urgencies(ranked, places)
    if 1 <= places <= len(ranked):
        cutoff = ranked[places - 1][1]

    disputed = Q(review_spread__gte=settings.REVIEW_DISPUTE_GAP)
    if cutoff is not None:
        # Different degrees of "clearly below" do not need more reviewers.
        disputed &= Q(online=True) | Q(review_low__lt=cutoff, review_high__gt=cutoff)
    return (
        applications.annotate(
            review_urgency=Case(
                When(disputed, then=Value(1.0)),
                *[When(pk__in=ids, then=Value(urgency)) for urgency, ids in urgencies.items()],
                default=Value(0.0), output_field=FloatField(),
            ),
        ).annotate(
            # Fractional targets round up: 50% urgency means ceil(5 + 7 * .5) = 9.
            review_target=Ceil(minimum + (maximum - minimum) * F('review_urgency')),
            review_priority=Case(When(review_count__lt=minimum, then=Value(2.0)),
                                 default=F('review_urgency'), output_field=FloatField()),
        ).filter(
            status=APP_PENDING,
            submission_date__lte=timezone.now() - timedelta(hours=2),
            review_count__lt=F('review_target'),
        )
        .exclude(Q(vote__user_id=user.pk) | Q(user_id=user.pk))
        .order_by('-review_priority', 'review_count', 'submission_date', 'pk')
    )


@transaction.atomic
def add_vote(application, user, tech_rat, pers_rat):
    """Recheck eligibility under a write lock, including votes from stale tabs."""
    # A no-op UPDATE locks the application on PostgreSQL and the writer on SQLite.
    # It must happen before reading the count; two reviewers cannot take the last slot.
    if not HackerApplication.objects.filter(pk=application.pk).update(status=F('status')):
        raise ValidationError('Application no longer exists.')
    # Vote.save recalculates this user's other votes; serialize their submissions too.
    User.objects.select_for_update().get(pk=user.pk)
    if not reviewable_applications(user).filter(pk=application.pk).exists():
        raise ValidationError('This application no longer needs your review. Showing the next one.')

    if tech_rat is not None or pers_rat is not None:
        try:
            tech_rat, pers_rat = int(tech_rat), int(pers_rat)
        except (TypeError, ValueError):
            raise ValidationError('Choose both scores before voting.')
        if not (1 <= tech_rat <= settings.MAX_VOTES and 1 <= pers_rat <= settings.MAX_VOTES):
            raise ValidationError('Scores must be between 1 and %s.' % settings.MAX_VOTES)

    vote = Vote.objects.create(application=application, user=user, tech=tech_rat, personal=pers_rat)
    # Skips do not approve a CV or count towards the review budget.
    votes_count = application.scored_vote_count
    application.refresh_from_db(fields=['cv_flagged'])
    if votes_count >= 5 and not application.cv_flagged:
        AcceptedResume.objects.update_or_create(application=application, defaults={'accepted': True})
    return vote
