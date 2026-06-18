import pytest
from unittest.mock import MagicMock, patch
from pipeline.neo4j_client import Neo4jManager


class TestNeo4jSecurity:
    @pytest.fixture
    def manager(self):
        with patch("src.pipeline.neo4j_client.GraphDatabase"):
            manager = Neo4jManager()
            # Mock the driver so it's not None
            manager._driver = MagicMock()
            return manager

    def test_get_community_summary_injection(self, manager):
        """Tests Cypher injection via category_type in get_community_summary."""
        injection_payload = "Media) DELETE (n"
        with pytest.raises(ValueError) as excinfo:
            manager.get_community_summary(injection_payload, "SomeName")
        assert "Unauthorized Cypher identifier" in str(excinfo.value)

    def test_multi_hop_traversal_injection(self, manager):
        """Tests Cypher injection via steps in multi_hop_traversal."""
        injection_payload = [
            "PRODUCED_BY",
            "HAS_THEME]->(n) DELETE (n) MATCH (start)-[:PRODUCED_BY",
        ]
        with pytest.raises(ValueError) as excinfo:
            manager.multi_hop_traversal("StartNode", injection_payload)
        assert "Unauthorized Cypher identifier" in str(excinfo.value)

    def test_verify_claims_injection(self, manager):
        """Tests Cypher injection via relation in verify_claims."""
        claims = [
            {
                "subject": "Naruto",
                "relation": "PRODUCED_BY]->(o) DELETE (s) MATCH (s)-[:PRODUCED_BY",
                "object": "Pierrot",
            }
        ]
        results = manager.verify_claims(claims)
        assert results[0]["verified"] is False
        assert results[0]["error"] == "Unauthorized relation type"

    def test_legitimate_labels_and_relations(self, manager):
        """Ensures legitimate identifiers are still allowed."""
        # Mocking session.run to avoid actual DB calls
        manager._driver.session.return_value.__enter__.return_value.run.return_value.single.return_value = {
            "total_works": 1,
            "top_themes": [],
            "key_studios": [],
        }

        # This should NOT raise ValueError
        try:
            manager.get_community_summary("Media", "Action")
            manager.multi_hop_traversal("Naruto", ["PRODUCED_BY"])
        except ValueError as e:
            pytest.fail(f"Legitimate identifier raised ValueError: {e}")
