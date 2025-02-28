# Generated by Django 3.2.23 on 2025-01-12 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0054_auto_20241231_0927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hackerapplication',
            name='graduation_year',
            field=models.IntegerField(choices=[(2024, '2024'), (2025, '2025'), (2026, '2026'), (2027, '2027'), (2028, '2028'), (2029, '2029'), (2030, '2030'), (2031, '2031')], default=2026),
        ),
        migrations.AlterField(
            model_name='mentorapplication',
            name='graduation_year',
            field=models.IntegerField(choices=[(2024, '2024'), (2025, '2025'), (2026, '2026'), (2027, '2027'), (2028, '2028'), (2029, '2029'), (2030, '2030'), (2031, '2031')], default=2026),
        ),
        migrations.AlterField(
            model_name='volunteerapplication',
            name='graduation_year',
            field=models.IntegerField(choices=[(2024, '2024'), (2025, '2025'), (2026, '2026'), (2027, '2027'), (2028, '2028'), (2029, '2029'), (2030, '2030'), (2031, '2031')], default=2026),
        ),
    ]
