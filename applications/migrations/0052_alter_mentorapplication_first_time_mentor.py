# Generated by Django 3.2.23 on 2024-12-14 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0051_merge_0049_auto_20240830_1617_0050_auto_20240830_1119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mentorapplication',
            name='first_time_mentor',
            field=models.BooleanField(blank=True),
        ),
    ]
