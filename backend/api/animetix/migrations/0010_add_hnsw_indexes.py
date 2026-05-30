from django.db import migrations

def create_hnsw_indexes(apps, schema_editor):
    """Désactivé : La logique vectorielle a été supprimée du projet."""
    return

def drop_hnsw_indexes(apps, schema_editor):
    """Désactivé : La logique vectorielle a été supprimée du projet."""
    return

class Migration(migrations.Migration):

    dependencies = [
        ('animetix', '0009_gameplaysession_user'),
    ]

    operations = [
        migrations.RunPython(create_hnsw_indexes, reverse_code=drop_hnsw_indexes),
    ]
