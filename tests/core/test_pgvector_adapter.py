import pytest
from unittest.mock import MagicMock
from adapters.persistence.pgvector_repository_adapter import PGVectorRepositoryAdapter

@pytest.mark.django_db
def test_pgvector_repository_adapter_operations():
    adapter = PGVectorRepositoryAdapter(project_root="")
    collection_name = "test_coll_repo"
    
    # Clean and insert test data
    adapter.delete_collection(collection_name)
    adapter.upsert_items(
        collection_name=collection_name,
        ids=["1", "2"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        metadatas=[{"title": "Anime A"}, {"title": "Anime B"}]
    )
    
    assert adapter.get_collection_count(collection_name) == 2
    assert sorted(adapter.get_all_ids(collection_name)) == ["1", "2"]
    
    # Calculate similarity (SQLite Numpy mode)
    score = adapter.calculate_similarity(collection_name, "1", "2")
    assert score == pytest.approx(0.0)
    
    # Search Nearest Neighbors
    neighbors = adapter.get_nearest_neighbors(collection_name, "1", n_results=1)
    assert neighbors["ids"][0][0] == "1"
