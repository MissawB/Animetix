import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from adapters.persistence.chroma_repository_adapter import ChromaRepositoryAdapter

@pytest.fixture
def repo(tmp_path):
    # Surgical patch of the CLIENT creation
    with patch("chromadb.PersistentClient") as mock_client:
        mock_client.return_value = MagicMock()
        repo_inst = ChromaRepositoryAdapter(db_path=str(tmp_path), project_root=str(tmp_path))
        repo_inst.client = mock_client.return_value
        yield repo_inst

def test_get_nearest_neighbors_success(repo):
    mock_coll = MagicMock()
    repo.client.get_or_create_collection.return_value = mock_coll
    
    # Bypass embedding_fn property
    repo._embedding_fn = MagicMock()
    
    # Ensure it returns a real DICT, not a Mock, to avoid internal Chroma/Rust type checks if any leak
    mock_coll.get.return_value = {'embeddings': [[0.1, 0.2]]}
    mock_coll.query.return_value = {'ids': [['2']], 'metadatas': [[{'title': 'Naruto'}]]}
    
    res = repo.get_nearest_neighbors("test_coll", "1")
    assert res == {'ids': [['2']], 'metadatas': [[{'title': 'Naruto'}]]}

def test_calculate_similarity_compute(repo):
    mock_coll = MagicMock()
    repo.client.get_or_create_collection.return_value = mock_coll
    repo._embedding_fn = MagicMock()
    
    mock_coll.get.return_value = {'embeddings': [[1, 0], [1, 0]]}
    
    res = repo.calculate_similarity("test", "1", "2")
    assert res == pytest.approx(1.0)

def test_get_collection_count(repo):
    mock_coll = MagicMock()
    repo.client.get_collection.return_value = mock_coll
    mock_coll.count.return_value = 10
    assert repo.get_collection_count("test") == 10

def test_get_all_ids(repo):
    mock_coll = MagicMock()
    repo.client.get_or_create_collection.return_value = mock_coll
    mock_coll.get.return_value = {'ids': ['1', '2']}
    assert repo.get_all_ids("test") == ['1', '2']
