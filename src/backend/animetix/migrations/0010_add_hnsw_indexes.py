from django.db import migrations

def create_hnsw_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS media_item_thematic_hnsw_idx ON animetix_mediaitem 
            USING hnsw (thematic_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS media_item_plot_hnsw_idx ON animetix_mediaitem 
            USING hnsw (plot_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS media_item_visual_hnsw_idx ON animetix_mediaitem 
            USING hnsw (visual_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)

def drop_hnsw_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS media_item_thematic_hnsw_idx;")
        cursor.execute("DROP INDEX IF EXISTS media_item_plot_hnsw_idx;")
        cursor.execute("DROP INDEX IF EXISTS media_item_visual_hnsw_idx;")

class Migration(migrations.Migration):

    dependencies = [
        ('animetix', '0009_gameplaysession_user'),
    ]

    operations = [
        migrations.RunPython(create_hnsw_indexes, reverse_code=drop_hnsw_indexes),
    ]
