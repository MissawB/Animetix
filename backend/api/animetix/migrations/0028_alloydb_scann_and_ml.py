from django.db import migrations, transaction


def _try_ddl(connection, sql, label):
    """Exécute un DDL optionnel (dépendant d'AlloyDB) sans casser la migration.

    Chaque instruction tourne dans son propre SAVEPOINT : sur un Postgres sans
    ces extensions (Neon), l'échec ne fait que rollback le savepoint — la
    transaction de migration reste valide et peut être commitée. Sans ça, un
    ``CREATE EXTENSION`` raté empoisonnait toute la transaction et faisait
    échouer le commit de la migration → migrate bloqué, migrations suivantes
    jamais appliquées.
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql)
    except Exception as e:
        print(f"Warning: {label}: {e}")


def setup_alloydb_features(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    connection = schema_editor.connection
    _try_ddl(
        connection,
        "CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE;",
        "Could not enable google_ml_integration",
    )
    _try_ddl(
        connection,
        "CREATE EXTENSION IF NOT EXISTS alloydb_scann CASCADE;",
        "Could not enable alloydb_scann",
    )
    _try_ddl(
        connection,
        "CREATE INDEX IF NOT EXISTS animetix_vectorrecord_embedding_scann_idx "
        "ON animetix_vectorrecord USING scann (embedding cosine) "
        "WITH (num_leaves = 100);",
        "Could not create ScaNN index",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("animetix", "0027_pgvector_migration"),
    ]
    operations = [
        migrations.RunPython(
            setup_alloydb_features, reverse_code=migrations.RunPython.noop
        ),
    ]
