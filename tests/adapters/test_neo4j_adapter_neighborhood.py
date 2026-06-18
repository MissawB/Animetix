import unittest
from unittest.mock import MagicMock
from adapters.persistence.neo4j_graph_adapter import Neo4jGraphAdapter


class TestNeo4jAdapterNeighborhood(unittest.TestCase):
    def setUp(self):
        self.mock_manager = MagicMock()
        self.adapter = Neo4jGraphAdapter(neo4j_manager=self.mock_manager)

    def test_get_neighborhood_calls_execute_query_with_correct_params(self):
        # Arrange
        item_id = "123"
        media_type = "anime"
        depth = 2

        mock_result = [
            {
                "nodes": [
                    {"id": 1, "properties": {"name": "Naruto"}, "labels": ["Anime"]}
                ],
                "links": [
                    {
                        "id": 10,
                        "source": 1,
                        "target": 2,
                        "type": "RELATED_TO",
                        "properties": {},
                    }
                ],
            }
        ]
        # Neo4jGraphAdapter calls self.execute_read which calls self._manager.execute_query
        self.mock_manager.execute_read.return_value = mock_result

        # Act
        result = self.adapter.get_neighborhood(item_id, media_type, depth)

        # Assert
        self.mock_manager.execute_read.assert_called_once()
        args, kwargs = self.mock_manager.execute_read.call_args
        query = args[0]
        params = args[1]

        self.assertIn("apoc.path.subgraphAll", query)
        self.assertIn("MATCH (start:Media {id: $id, type: $type})", query)
        self.assertEqual(params["id"], item_id)
        self.assertEqual(params["type"], media_type)
        self.assertEqual(params["depth"], depth)
        self.assertEqual(result, mock_result[0])

    def test_get_neighborhood_returns_empty_on_no_results(self):
        # Arrange
        self.mock_manager.execute_read.return_value = []

        # Act
        result = self.adapter.get_neighborhood("nonexistent", "movie")

        # Assert
        self.assertEqual(result, {"nodes": [], "links": []})

    def test_get_neighborhood_handles_exception(self):
        # Arrange
        self.mock_manager.execute_read.side_effect = Exception("Neo4j error")

        # Act
        result = self.adapter.get_neighborhood("error", "anime")

        # Assert
        self.assertEqual(result, {"nodes": [], "links": []})


if __name__ == "__main__":
    unittest.main()
