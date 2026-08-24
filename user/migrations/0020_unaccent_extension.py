from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0019_user_mlh_subscribed'),
    ]

    operations = [
        UnaccentExtension(),
    ]
