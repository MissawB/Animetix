from django.db import migrations


def setup_alloydb_features(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        # Enable google_ml_integration
        try:
            cursor.execute(
                "CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE;"
            )
        except Exception as e:
            print(f"Warning: Could not enable google_ml_integration: {e}")

        # Enable alloydb_scann
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS alloydb_scann CASCADE;")
        except Exception as e:
            print(f"Warning: Could not enable alloydb_scann: {e}")

        # Create ScaNN index on VectorRecord embedding column
        try:
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS animetix_vectorrecord_embedding_scann_idx "
                "ON animetix_vectorrecord USING scann (embedding cosine) "
                "WITH (num_leaves = 100);"
            )
        except Exception as e:
            print(f"Warning: Could not create ScaNN index: {e}")


class Migration(migrations.Migration):
    dependencies = [
        ("animetix", "0027_pgvector_migration"),
    ]
    operations = [
        migrations.RunPython(
            setup_alloydb_features, reverse_code=migrations.RunPython.noop
        ),
    ]
