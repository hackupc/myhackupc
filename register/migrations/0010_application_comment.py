# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-04 06:59
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('register', '0009_vegan'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='register.Application')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='hacker',
            name='graduation_year',
            field=models.IntegerField(choices=[(2016, '2016'), (2017, '2017'), (2018, '2018'), (2019, '2019')]),
        ),
    ]