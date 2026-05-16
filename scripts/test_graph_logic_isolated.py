import sys
import os
from unittest.mock import MagicMock
import json

# Force mock modules for heavy libraries that are broken in this env
class Mocked: pass
sys.modules['neo4j'] = Mocked()
sys.modules['sentence_transformers'] = Mocked()
sys.modules['pandas'] = Mocked()
sys.modules['torch'] = Mocked()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.domain.services.graph_construction_service import KnowledgeGraphConstructionService

def run_isolated_test():
    print("🧪 Starting Isolated AI Logic Test...")
    
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
    service = KnowledgeGraphConstructionService(inference_engine=mock_engine)
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
