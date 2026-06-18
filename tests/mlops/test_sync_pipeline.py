import json
import os
from unittest.mock import MagicMock, patch

import pytest
from scripts.sync_gold_ground_truth import (
    run_synchronization,
    update_regression_benchmark_file,
)


@pytest.fixture
def mock_neo4j():
    mock = MagicMock()
    mock.check_health.return_value = True

    # Mock node properties and relationship results
    mock_props = {"title": "Demon Slayer", "episodes": 74}

    def mock_execute_read(query, parameters=None):
        if "MATCH (m) WHERE m.id" in query:
            return [{"props": mock_props, "labels": ["Media"]}]
        elif "MATCH (m)-[r]->(target)" in query:
            return [
                {
                    "rel_type": "PRODUCED_BY",
                    "target_name": "ufotable",
                    "target_title": None,
                    "target_labels": ["Studio"],
                }
            ]
        return []

    mock.execute_read.side_effect = mock_execute_read
    return mock


@pytest.fixture
def mock_inference_engine():
    mock = MagicMock()

    # Mock factual check response (CurationSyncSchema)
    mock_sync_result = MagicMock()
    mock_sync_result.is_accurate = False
    mock_sync_result.updated_ground_truth = (
        "Demon Slayer has 74 episodes and is produced by ufotable."
    )
    mock_sync_result.reasoning = "Episode count updated from 63 to 74 in the database."

    # Mock expected facts response (ExpectedFactsSchema)
    mock_facts_result = MagicMock()
    mock_facts_result.expected_facts = [["74 episodes", "74 épisodes"], "ufotable"]

    mock.generate_structured.side_effect = [mock_sync_result, mock_facts_result]
    return mock


@pytest.mark.django_db
@patch("scripts.sync_gold_ground_truth.get_container")
def test_sync_gold_ground_truth_pipeline(
    mock_get_container, mock_neo4j, mock_inference_engine, tmp_path
):
    # Setup mock gold dataset
    mock_gold_data = [
        {
            "query": "Combien d'épisodes compte Demon Slayer ?",
            "ground_truth": "Demon Slayer compte 63 épisodes.",
            "expected_id": "38000",
            "expected_entities": ["Demon Slayer"],
        }
    ]

    os.makedirs(os.path.join(tmp_path, "data", "mlops"), exist_ok=True)
    real_mock_gold_path = os.path.join(tmp_path, "data", "mlops", "gold_dataset.json")

    with open(real_mock_gold_path, "w", encoding="utf-8") as f:
        json.dump(mock_gold_data, f)

    # Setup mock container
    mock_container = MagicMock()
    mock_container.persistence.graph_persistence_port.return_value = mock_neo4j
    mock_container.inference_engine.return_value = mock_inference_engine
    mock_get_container.return_value = mock_container

    # Mock benchmark list GOLD_SET
    mock_benchmark_gold_set = [
        {
            "query": "Combien d'épisodes compte Demon Slayer ?",
            "expected_facts": [["63 épisodes"]],
            "media_type": "Anime",
        }
    ]

    # Path patch
    with (
        patch("scripts.sync_gold_ground_truth.PROJECT_ROOT", str(tmp_path)),
        patch(
            "backend.pipeline.evaluation.regression_benchmark.GOLD_SET",
            mock_benchmark_gold_set,
        ),
        patch(
            "scripts.sync_gold_ground_truth.update_regression_benchmark_file"
        ) as mock_update_file,
    ):
        res = run_synchronization(dry_run=False)

        assert res["status"] == "success"
        assert res["updated_count"] == 1

        # Verify gold dataset file was updated
        with open(real_mock_gold_path, "r", encoding="utf-8") as f:
            updated_data = json.load(f)

        assert (
            updated_data[0]["ground_truth"]
            == "Demon Slayer has 74 episodes and is produced by ufotable."
        )

        # Verify that update_regression_benchmark_file was called
        mock_update_file.assert_called_once()
        args, _ = mock_update_file.call_args
        updated_benchmark_list = args[0]
        assert updated_benchmark_list[0]["expected_facts"] == [
            ["74 episodes", "74 épisodes"],
            "ufotable",
        ]


def test_update_regression_benchmark_file(tmp_path):
    # Create mock regression_benchmark.py
    mock_file_content = """
import os  # noqa: E402
import sys  # noqa: E402

GOLD_SET = [
    {
        "query": "Test query",
        "expected_facts": ["old_fact"],
        "media_type": "Anime"
    }
]

def run_regression_test():
    pass
"""

    os.makedirs(
        os.path.join(tmp_path, "backend", "pipeline", "evaluation"), exist_ok=True
    )
    real_file_path = os.path.join(
        tmp_path, "backend", "pipeline", "evaluation", "regression_benchmark.py"
    )
    with open(real_file_path, "w", encoding="utf-8") as f:
        f.write(mock_file_content)

    new_gold_set = [
        {"query": "Test query", "expected_facts": ["new_fact"], "media_type": "Anime"}
    ]

    with patch("scripts.sync_gold_ground_truth.PROJECT_ROOT", str(tmp_path)):
        update_regression_benchmark_file(new_gold_set)

        with open(real_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "new_fact" in updated_content
        assert "old_fact" not in updated_content
        assert "GOLD_SET = [" in updated_content
