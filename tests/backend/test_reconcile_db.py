"""`reconcile_db` must not issue a clean bill of health for a store it never
checked. A dead Neo4j URI (the local instance no longer resolves) makes the
command skip every graph check — but the old verdict still printed
"[SUCCESS] All sampled items are synchronized across Django, pgvector, and
Neo4j", so the skip went unnoticed. The verdict must reflect what was actually
verified.
"""

import io

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_reconcile_db_does_not_claim_neo4j_sync_when_offline(mocker):
    from animetix.models import MediaItem, VectorRecord

    # Actor has a single vibe collection -> easy to make pgvector-complete so
    # the ONLY reason the run could be clean is that Neo4j was skipped.
    MediaItem.objects.create(external_id="x1", media_type="Actor", title="Seiyuu")
    VectorRecord.objects.create(collection_name="actor_vibe", item_id="x1", metadata={})

    import animetix.management.commands.reconcile_db as cmd

    offline_neo4j = mocker.MagicMock()
    offline_neo4j.driver = None  # dead URI -> driver never came up
    mocker.patch.object(cmd, "neo4j_manager", offline_neo4j)

    online_vector = mocker.MagicMock()
    online_vector.get_collection.return_value = object()
    mocker.patch.object(cmd, "vector_manager", online_vector)

    out = io.StringIO()
    call_command("reconcile_db", stdout=out)
    output = out.getvalue()

    # The false all-clear must be gone...
    assert "synchronized across Django, pgvector, and Neo4j" not in output
    # ...and the verdict must say Neo4j's sync is UNVERIFIED, not confirmed.
    assert "UNVERIFIED" in output


@pytest.mark.django_db
def test_reconcile_db_reports_full_success_when_every_store_is_checked(mocker):
    from animetix.models import MediaItem, VectorRecord

    MediaItem.objects.create(external_id="x1", media_type="Actor", title="Seiyuu")
    VectorRecord.objects.create(collection_name="actor_vibe", item_id="x1", metadata={})

    import animetix.management.commands.reconcile_db as cmd

    online_neo4j = mocker.MagicMock()
    online_neo4j.driver = object()  # connected
    online_neo4j.execute_query.return_value = [{"n": 1}]  # item present in graph
    mocker.patch.object(cmd, "neo4j_manager", online_neo4j)

    online_vector = mocker.MagicMock()
    online_vector.get_collection.return_value = object()
    mocker.patch.object(cmd, "vector_manager", online_vector)

    out = io.StringIO()
    call_command("reconcile_db", stdout=out)
    output = out.getvalue()

    assert "synchronized across Django, pgvector, and Neo4j" in output
    assert "UNVERIFIED" not in output
