# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-07-09 08:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judging', '0008_auto_20191013_0956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentationevaluation',
            name='design',
            field=models.IntegerField(choices=[(0, '0'), (1, '1')]),
        ),
        migrations.AlterField(
            model_name='presentationevaluation',
            name='smoke',
            field=models.IntegerField(choices=[(0, '0'), (1, '1')]),
        ),
        migrations.AlterField(
            model_name='presentationevaluation',
            name='ux',
            field=models.IntegerField(choices=[(0, '0'), (1, '1')]),
        ),
    ]
