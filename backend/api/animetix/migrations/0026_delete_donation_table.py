# Generated manually on 2026-06-01

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("animetix", "0025_profile_personalization_settings"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS animetix_donation;", reverse_sql=""
        ),
    ]
