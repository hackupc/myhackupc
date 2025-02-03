import random

from django.db import models

from user.models import User

TEAM_ID_LENGTH = 13


def generate_team_id():
    s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    while True:
        team_id = "".join(random.sample(s, TEAM_ID_LENGTH))
        if not Team.objects.filter(team_code=team_id).exists():
            return team_id


class Team(models.Model):
    team_code = models.CharField(default=generate_team_id, max_length=TEAM_ID_LENGTH)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("team_code", "user"),)
