import random
import string, uuid
from django.db import models
from user.models import User

MAX_LENGTH_TEAM_CODE = 36


def generate_team_id():
    return str(uuid.uuid4())


class Team(models.Model):
    """
    This model represents a team of hackers. For each hacker in a team, there is one entry
    in this table with the same team_code. The user field is a foreign key to the user
    """

    team_code = models.CharField(
        default=generate_team_id, max_length=MAX_LENGTH_TEAM_CODE
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("team_code", "user"),)
