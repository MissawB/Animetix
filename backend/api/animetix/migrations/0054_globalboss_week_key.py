"""Le spawn hebdomadaire devient idempotent : une semaine ISO, un seul raid.

`_active_boss()` était un read-then-create sans verrou : deux requêtes tombant
dans la fenêtre vide — celle que la migration 0051 ouvre AU DÉPLOIEMENT en
expirant le boss legacy, et dans laquelle la bannière d'accueil, la requête de la
page et POST /question/ frappent en même temps — invoquaient chacune leur raid de
100 000 PV. Les participations étant liées au boss par FK, dégâts, classement et
XP se scindaient entre deux raids que personne ne pouvait plus achever.

`week_key` unique + `get_or_create(week_key=...)` : la course se résout en base.

Les raids déjà en table reçoivent une clé qui ne peut entrer en collision avec
aucune semaine ISO (« legacy-<id> ») : ils ne doivent jamais être confondus avec
le raid de la semaine en cours, ni bloquer sa création.
"""

from django.db import migrations, models


def key_the_existing_raids(apps, schema_editor):
    GlobalBoss = apps.get_model("animetix", "GlobalBoss")
    for boss in GlobalBoss.objects.all():
        boss.week_key = f"legacy-{boss.id}"
        boss.save(update_fields=["week_key"])


def unkey(apps, schema_editor):
    GlobalBoss = apps.get_model("animetix", "GlobalBoss")
    GlobalBoss.objects.update(week_key=None)


class Migration(migrations.Migration):

    dependencies = [
        ("animetix", "0053_bossparticipation_unique_user_boss"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalboss",
            name="week_key",
            field=models.CharField(blank=True, default=None, max_length=32, null=True),
        ),
        migrations.RunPython(key_the_existing_raids, unkey),
        migrations.AlterField(
            model_name="globalboss",
            name="week_key",
            field=models.CharField(
                blank=True, default=None, max_length=32, null=True, unique=True
            ),
        ),
    ]
