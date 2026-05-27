import unittest
from unittest.mock import MagicMock
from core.domain.services.graph_healer_service import GraphHealerService

class TestGraphHealerService(unittest.TestCase):
    def test_ensure_graph_integrity_success(self):
        mock_neo4j = MagicMock()
        mock_neo4j.driver = True
        mock_neo4j.execute_query.return_value = [{"id": "1"}]
        
        mock_construction = MagicMock()
        mock_repo = MagicMock()
        mock_engine = MagicMock()
        
        service = GraphHealerService(
            neo4j_manager=mock_neo4j,
            construction_service=mock_construction,
            repository=mock_repo,
            inference_engine=mock_engine
        )
        
        # Should identify id 2 as missing and heal it
        mock_repo.get_media_by_id.return_value = {"title": "Title", "description": "Short", "media_type": "Anime"}
        service.ensure_graph_integrity(["1", "2"])
        
        mock_neo4j.execute_query.assert_called_once()
        mock_repo.get_media_by_id.assert_called_once_with("2")
