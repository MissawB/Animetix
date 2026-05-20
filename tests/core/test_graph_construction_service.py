import pytest
from unittest.mock import MagicMock
from core.domain.services.graph_construction_service import KnowledgeGraphConstructionService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_prompt_manager():
    manager = MagicMock()
    manager.get_prompt.return_value = ("Formatted Prompt", "System Prompt")
    return manager

@pytest.fixture
def graph_builder(mock_engine, mock_prompt_manager):
    return KnowledgeGraphConstructionService(inference_engine=mock_engine, prompt_manager=mock_prompt_manager)

def test_extract_entities_and_relations_success(graph_builder, mock_engine, mock_prompt_manager):
    from core.domain.entities.ai_schemas import GraphExtraction, GraphEntity, GraphRelation
    
    mock_extraction = GraphExtraction(
        entities=[GraphEntity(name="Naruto", type="Person", description="Ninja")],
        relations=[GraphRelation(source="Naruto", target="Konoha", relation="LOCATED_IN", description="Lives there")]
    )
    
    mock_engine.generate_structured.return_value = mock_extraction
    
    res = graph_builder.extract_entities_and_relations("Naruto", "Ninja story", "Anime")
    
    mock_prompt_manager.get_prompt.assert_called_once_with(
        "graph_construction",
        title="Naruto",
        media_type="Anime",
        description="Ninja story"
    )
    
    assert len(res['entities']) == 1
    assert res['entities'][0]['name'] == "Naruto"
    assert res['relations'][0]['relation'] == "LOCATED_IN"
