from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("animetix", "0010_add_hnsw_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mediaitem",
            name="thematic_embedding",
            field=models.JSONField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="mediaitem",
            name="plot_embedding",
            field=models.JSONField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="mediaitem",
            name="visual_embedding",
            field=models.JSONField(null=True, blank=True),
        ),
    ]
