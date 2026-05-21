import sys
import os
from unittest.mock import MagicMock
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

def run_isolated_test():
    print("🧪 Starting Isolated AI Logic Test...")
    
    # Force mock modules for heavy libraries that are broken in this env
    class Mocked: pass
    sys.modules['neo4j'] = Mocked()
    sys.modules['sentence_transformers'] = Mocked()
    sys.modules['pandas'] = Mocked()
    sys.modules['torch'] = Mocked()
    
    from core.domain.services.graph_construction_service import KnowledgeGraphConstructionService
    
    # 1. Setup Mock Engine
    mock_engine = MagicMock()
    mock_engine.generate.return_value = json.dumps({
        "entities": [
            {"name": "Goku", "type": "Person", "description": "Saiyan"},
            {"name": "Vegeta", "type": "Person", "description": "Prince"}
        ],
        "relations": [
            {"source": "Goku", "target": "Vegeta", "type": "ENEMY_OF"}
        ]
    })

    # 2. Test Extraction
    mock_prompt_manager = MagicMock()
    mock_prompt_manager.get_prompt.return_value = ("Prompt", "System")
    service = KnowledgeGraphConstructionService(inference_engine=mock_engine, prompt_manager=mock_prompt_manager)
    extracted = service.extract_entities_and_relations(
        title="Dragon Ball",
        description="Goku combats Vegeta.",
        media_type="Anime"
    )

    # 3. Assertions
    try:
        assert len(extracted['entities']) == 2
        assert extracted['relations'][0]['type'] == "ENEMY_OF"
        print("✅ SUCCESS: AI Extraction Logic is functional!")
    except Exception as e:
        print(f"❌ FAILURE: {e}")
        print(f"Result was: {extracted}")

if __name__ == "__main__":
    run_isolated_test()
