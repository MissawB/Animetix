import pytest
from unittest.mock import MagicMock, patch
import json

# Mocking heavy dependencies before imports
import sys
from unittest.mock import Mock

mock_neo4j = Mock()
sys.modules['neo4j'] = mock_neo4j
sys.modules['pipeline.neo4j_client'] = Mock(neo4j_manager=Mock())

from src.core.domain.services.graph_construction_service import KnowledgeGraphConstructionService

@pytest.fixture
def mock_inference_engine():
    engine = MagicMock()
    # Simulated LLM response for a typical anime synopsis
    mock_model = MagicMock()
    mock_model.model_dump.return_value = {
        "entities": [
            {"name": "Naruto Uzumaki", "type": "Person", "description": "Protagoniste"},
            {"name": "Sasuke Uchiha", "type": "Person", "description": "Rival"}
        ],
        "relations": [
            {"source": "Naruto Uzumaki", "target": "Sasuke Uchiha", "type": "ENEMY_OF"}
        ]
    }
    engine.generate_structured.return_value = mock_model
    return engine

def test_graph_extraction_logic(mock_inference_engine):
    mock_prompt_manager = MagicMock()
    mock_prompt_manager.get_prompt.return_value = ("Prompt", "System")
    service = KnowledgeGraphConstructionService(inference_engine=mock_inference_engine, prompt_manager=mock_prompt_manager)
    
    extracted = service.extract_entities_and_relations(
        title="Naruto",
        description="L'histoire d'un jeune ninja qui veut devenir Hokage et de son rival Sasuke.",
        media_type="Anime"
    )
    
    assert len(extracted['entities']) == 2
    assert extracted['relations'][0]['type'] == "ENEMY_OF"
    assert extracted['relations'][0]['source'] == "Naruto Uzumaki"

@patch('src.pipeline.enrich_graph_ai.neo4j_manager')
def test_enrichment_pipeline_sync_call(mock_neo4j_mgr, mock_inference_engine):
    from src.pipeline.enrich_graph_ai import enrich_media_type
    
    # Mocking the container to return our mock service
    mock_container = MagicMock()
    mock_prompt_manager = MagicMock()
    mock_prompt_manager.get_prompt.return_value = ("prompt", "system")
    mock_container.graph_builder = KnowledgeGraphConstructionService(inference_engine=mock_inference_engine, prompt_manager=mock_prompt_manager)    
    with patch('src.pipeline.enrich_graph_ai.get_container', return_value=mock_container):
        # We simulate a small catalog
        sample_data = [{"id": 1, "title": "Naruto", "description": "Un synopsis assez long pour passer le filtre de longueur de 100 caracteres."}]
        
        with patch('builtins.open', MagicMock()):
            with patch('json.load', return_value=[{"id": 1, "title": "Naruto", "description": "L'histoire d'un jeune ninja qui veut devenir Hokage et de son rival Sasuke qui souhaite restaurer son clan. C'est une épopée légendaire de 500 épisodes qui commence au village de Konoha."}]):
                enrich_media_type("Anime", limit=1)
                
                # Check if neo4j injection was called with extracted data
                mock_neo4j_mgr.sync_ai_extracted_graph.assert_called_once()
                call_args = mock_neo4j_mgr.sync_ai_extracted_graph.call_args
                assert call_args[0][0] == "1" # media_id
                assert len(call_args[0][1]['entities']) == 2
