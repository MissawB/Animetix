import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure correct backend imports
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
if os.path.join(PROJECT_ROOT, "backend", "api") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "api"))


@pytest.fixture
def mock_neo4j():
    with patch("pipeline.neo4j_client.neo4j_manager") as mock:
        mock_session = MagicMock()
        mock_record1 = {"title": "Death Note", "id": "1535"}
        mock_record2 = {"title": "Bleach", "id": "154"}
        mock_session.run.return_value = [mock_record1, mock_record2]

        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock.driver = mock_driver

        # Add mocks for the GraphPersistencePort interface
        mock.check_health.return_value = True

        def mock_execute_read(query, parameters=None):
            if "MATCH (m:Media)" in query and "id: $mid" not in query:
                return [mock_record1, mock_record2]
            elif "MATCH (m:Media {id: $mid})" in query or "id: $mid" in query:
                if parameters and parameters.get("mid") == "154":
                    return [
                        {
                            "rel_type": "CREATED_BY",
                            "target_name": "Tite Kubo",
                            "target_title": None,
                        }
                    ]
                return []
            return []

        mock.execute_read.side_effect = mock_execute_read
        yield mock


@pytest.fixture
def mock_inference_engine(mock_neo4j):
    with patch("animetix.containers.get_container") as mock_container:
        mock_engine = MagicMock()
        mock_result = MagicMock()
        mock_result.dict.return_value = {
            "query": "Quel est l'auteur de Bleach ?",
            "ground_truth": "Tite Kubo",
            "expected_entities": ["Bleach", "Tite Kubo"],
            "expected_contexts": ["Bleach est un manga de Tite Kubo."],
            "expected_chunks": ["154"],
            "query_type": "graph",
            "difficulty": "easy",
        }
        mock_engine.generate_structured.return_value = mock_result

        mock_container_instance = MagicMock()
        mock_container_instance.inference.inference_engine.return_value = mock_engine
        mock_container_instance.persistence.graph_persistence_port.return_value = (
            mock_neo4j
        )
        mock_container.return_value = mock_container_instance
        yield mock_engine


@pytest.mark.django_db
def test_analyze_coverage_identifies_gaps(mock_neo4j, mock_inference_engine, tmp_path):
    # Setup mock gold dataset
    mock_gold_data = [
        {
            "query": "Qui est Light Yagami dans Death Note ?",
            "expected_entities": ["Death Note", "Light Yagami"],
            "domain": "shonen",
            "query_type": "standard",
            "ground_truth": "Light Yagami est le protagoniste de Death Note.",
        }
    ]

    tmp_path / "gold_dataset.json"
    os.makedirs(os.path.join(tmp_path, "data", "mlops"), exist_ok=True)
    mock_gold_path = os.path.join(tmp_path, "data", "mlops", "gold_dataset.json")
    with open(mock_gold_path, "w", encoding="utf-8") as f:
        json.dump(mock_gold_data, f)

    with patch("scripts.analyze_gold_coverage.PROJECT_ROOT", str(tmp_path)):
        # Import inside patch
        from scripts.analyze_gold_coverage import (  # noqa: E402
            analyze_coverage,
            generate_and_append_missing,
        )

        # Verify coverage identification
        report = analyze_coverage(threshold=0.01)
        assert len(report["missing_media"]) > 0

        # Verify title 'Bleach' is missing, but 'Death Note' is not
        missing_titles = [m["title"] for m in report["missing_media"]]
        assert "Bleach" in missing_titles
        assert "Death Note" not in missing_titles

        # Run generation
        generate_and_append_missing(report)

        # Verify it appended Bleach entry
        with open(mock_gold_path, "r", encoding="utf-8") as f:
            updated_data = json.load(f)

        assert len(updated_data) > len(mock_gold_data)
        assert updated_data[-1]["query"] == "Quel est l'auteur de Bleach ?"
