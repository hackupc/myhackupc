from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0020_unaccent_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_hx',
            field=models.BooleanField(default=False, verbose_name='Can modify CV'),
        ),
    ]
