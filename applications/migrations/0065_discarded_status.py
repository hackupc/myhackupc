from django.db import migrations, models


STATUS_CHOICES = [
    ("P", "Under review"),
    ("R", "Wait listed"),
    ("I", "Invited"),
    ("LR", "Last reminder"),
    ("C", "Confirmed"),
    ("X", "Cancelled"),
    ("A", "Attended"),
    ("E", "Expired"),
    ("D", "Dubious"),
    ("IV", "Invalid"),
    ("BL", "Blacklisted"),
    ("DC", "Discarded"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0064_auto_20260118_1201"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hackerapplication",
            name="status",
            field=models.CharField(
                choices=STATUS_CHOICES, default="P", max_length=2
            ),
        ),
        migrations.AlterField(
            model_name="mentorapplication",
            name="status",
            field=models.CharField(
                choices=STATUS_CHOICES, default="P", max_length=2
            ),
        ),
        migrations.AlterField(
            model_name="volunteerapplication",
            name="status",
            field=models.CharField(
                choices=STATUS_CHOICES, default="P", max_length=2
            ),
        ),
        migrations.AlterField(
            model_name="sponsorapplication",
            name="status",
            field=models.CharField(
                choices=STATUS_CHOICES, default="C", max_length=2
            ),
        ),
    ]
