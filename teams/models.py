import random
import string
from django.db import models, IntegrityError, transaction
from user.models import User

TEAM_ID_LENGTH = 13
MAX_ATTEMPTS = 33

def generate_team_id():
    s = string.ascii_letters + string.digits  # 62 caràcters únics
    for _ in range(MAX_ATTEMPTS):
        team_id = "".join(random.choices(s, k=TEAM_ID_LENGTH))
        if not Team.objects.filter(team_code=team_id).exists():
            return team_id
    raise Exception("No s'ha pogut generar un team_code únic després de diversos intents.")

class Team(models.Model):
    team_code = models.CharField(default=generate_team_id, max_length=TEAM_ID_LENGTH)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("team_code", "user"),)
