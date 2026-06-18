import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "animetix",
            "0008_alter_mediaitem_options_remove_airevalresult_context_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="gameplaysession",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="auth.user",
            ),
        ),
    ]
