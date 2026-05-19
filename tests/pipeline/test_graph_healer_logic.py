import pytest
import os
import json
from unittest.mock import MagicMock, patch
from pipeline.mlops.graph_healer import run_graph_healer

@pytest.fixture
def mock_django_models(mocker):
    mock_ticket = mocker.patch('animetix.models.DataCurationTicket.objects.get_or_create')
    mock_ticket.return_value = (MagicMock(), True)
    return mock_ticket

@pytest.fixture
def mock_neo4j(mocker):
    mock_manager = mocker.patch('pipeline.neo4j_client.neo4j_manager')
    return mock_manager

def test_run_graph_healer_no_anomalies(mock_django_models, mock_neo4j, tmp_path, mocker):
    # Setup mock ground truth DB
    db_file = tmp_path / "clean_root_animes.json"
    data = [{"title": "Naruto", "studios": ["Pierrot"]}]
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    # Mock Neo4j to match PG
    mock_neo4j.execute_query.return_value = [{"studio_name": "Pierrot"}]
    
    with patch('pipeline.mlops.graph_healer.BASE_DIR', str(tmp_path.parent.parent)): # Adjust BASE_DIR
        # We need to monkeypatch the actual path used in the function
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mocker.mock_open(read_data=json.dumps(data))):
            
            run_graph_healer(limit=1)
            
            # Should NOT create any tickets
            assert mock_django_models.call_count == 0

def test_run_graph_healer_with_anomaly(mock_django_models, mock_neo4j, tmp_path):
    data = [{"title": "One Piece", "studios": ["Toei Animation"]}]
    
    # Mock Neo4j to NOT match PG (missing studio)
    mock_neo4j.execute_query.return_value = []
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', pytest.importorskip("unittest.mock").mock_open(read_data=json.dumps(data))):
        
        run_graph_healer(limit=1)
        
        # Should create a ticket
        assert mock_django_models.call_count == 1
        args, kwargs = mock_django_models.call_args
        assert kwargs['item_title'] == "One Piece"
        assert "Contradiction" in kwargs['defaults']['issue_description']
