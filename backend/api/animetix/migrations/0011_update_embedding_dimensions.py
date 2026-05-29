from django.db import migrations, models
try:
    from pgvector.django import VectorField
except ImportError:
    class VectorField(models.JSONField):
        def __init__(self, *args, **kwargs):
            kwargs.pop('dimensions', None)
            super().__init__(*args, **kwargs)

class Migration(migrations.Migration):

    dependencies = [
        ('animetix', '0010_add_hnsw_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediaitem',
            name='thematic_embedding',
            field=VectorField(dimensions=1024, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='mediaitem',
            name='plot_embedding',
            field=VectorField(dimensions=1024, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='mediaitem',
            name='visual_embedding',
            field=VectorField(dimensions=1152, null=True, blank=True),
        ),
    ]
