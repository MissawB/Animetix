import unittest
from unittest.mock import MagicMock, patch
from core.domain.services.graph_healer_service import GraphHealerService

class TestGraphHealerService(unittest.TestCase):
    @patch('core.domain.services.graph_healer_service.run_graph_healer')
    def test_perform_healing_success(self, mock_run):
        service = GraphHealerService()
        result = service.perform_healing(limit=10)
        
        self.assertEqual(result["status"], "success")
        mock_run.assert_called_once_with(limit=10)

    @patch('core.domain.services.graph_healer_service.run_graph_healer')
    def test_perform_healing_error(self, mock_run):
        mock_run.side_effect = Exception("DB Fail")
        service = GraphHealerService()
        result = service.perform_healing()
        
        self.assertEqual(result["status"], "error")
