from math import sqrt

from django.conf import settings
from django.db import migrations
from django.db.models import Avg, F


def recalculate_votes(apps, schema_editor):
    Vote = apps.get_model('organizers', 'Vote')
    votes = Vote.objects.using(schema_editor.connection.alias)
    # Deleted reviewers cannot be reconstructed: their votes all have user=NULL.
    # Preserve those scores rather than treating them as one shared reviewer.
    user_ids = list(votes.exclude(user_id=None).order_by()
                    .values_list('user_id', flat=True).distinct())
    scale = getattr(settings, 'MAX_VOTES', 5) / 10
    for user_id in user_ids:
        user_votes = votes.filter(user_id=user_id)
        means = user_votes.aggregate(tech=Avg('tech'), personal=Avg('personal'))
        if means['tech'] is None or means['personal'] is None:
            continue
        tech_delta = F('tech') - means['tech']
        personal_delta = F('personal') - means['personal']
        variances = user_votes.aggregate(
            tech=Avg(tech_delta * tech_delta),
            personal=Avg(personal_delta * personal_delta),
        )
        tech = 0.2 * tech_delta / (sqrt(variances['tech']) or 1.0)
        personal = 0.8 * personal_delta / (sqrt(variances['personal']) or 1.0)
        user_votes.update(calculated_vote=(personal + tech) * scale)


class Migration(migrations.Migration):
    dependencies = [('organizers', '0005_alter_vote_user')]

    # Raw marks are retained, but the previous derived scores are not backed up.
    operations = [migrations.RunPython(recalculate_votes)]
