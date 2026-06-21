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
            inference_engine=mock_engine,
        )

        # Should identify id 2 as missing and heal it
        mock_repo.get_media_by_id.return_value = {
            "title": "Title",
            "description": "Short",
            "media_type": "Anime",
        }
        service.ensure_graph_integrity(["1", "2"])

        mock_neo4j.execute_query.assert_called_once()
        mock_repo.get_media_by_id.assert_called_once_with("2")

    def test_audit_graph_quality_with_duplicates(self):
        mock_neo4j = MagicMock()
        mock_neo4j.driver = True
        mock_neo4j.execute_query.side_effect = [
            [{"count": 5}],
            [{"t1": "Seq", "y1": 2000, "t2": "Orig", "y2": 2010}],
            [{"count": 3}],
            [{"dup_count": 4}],
        ]

        service = GraphHealerService(
            neo4j_manager=mock_neo4j,
            construction_service=MagicMock(),
            repository=MagicMock(),
            inference_engine=MagicMock(),
        )

        res = service.audit_graph_quality()
        self.assertEqual(res["isolated_nodes"], 5)
        self.assertEqual(res["temporal_conflicts"], 1)
        self.assertEqual(res["orphan_entities"], 3)
        self.assertEqual(res["duplicate_entities"], 4)

    def test_merge_duplicate_entities_success(self):
        mock_neo4j = MagicMock()
        mock_neo4j.driver = True
        mock_neo4j.execute_query.side_effect = [
            [{"val": "Goku", "ids": [10, 11]}],
            [{"count": 1}],
        ]

        service = GraphHealerService(
            neo4j_manager=mock_neo4j,
            construction_service=MagicMock(),
            repository=MagicMock(),
            inference_engine=MagicMock(),
        )

        merged = service.merge_duplicate_entities()
        self.assertEqual(merged, 1)
        mock_neo4j.execute_query.assert_any_call(
            "\n        MATCH (n:Entity)\n        WITH n.name AS val, collect(n) AS nodes, count(*) AS count\n        WHERE count > 1 AND val IS NOT NULL\n        RETURN val, [node IN nodes | id(node)] AS ids\n        "
        )
