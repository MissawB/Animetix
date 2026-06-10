# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from core.domain.services.domain_synthesizer import AutonomousDomainSynthesizer
from core.domain.services.distillation_pipeline import ModelDistillationPipeline
from core.domain.services.synthetic_promotion_service import SyntheticDataPromotionService
from core.ports.gold_dataset_port import GoldDatasetPort

@pytest.fixture
def mock_gold_port():
    port = MagicMock(spec=GoldDatasetPort)
    # Simulation d'une base de données en mémoire pour le test
    port.entries = []
    
    def save_synthetic_entry(entry_type, context, instruction, response, metadata=None):
        entry = {
            "id": len(port.entries) + 1,
            "entry_type": entry_type,
            "context": context,
            "instruction": instruction,
            "response": response,
            "metadata": metadata,
            "is_validated": False
        }
        port.entries.append(entry)
        return entry["id"]

    def get_unprocessed_validated_entries():
        return [e for e in port.entries if e["is_validated"]]

    def mark_entries_as_processed(ids):
        port.entries = [e for e in port.entries if e["id"] not in ids]

    port.save_synthetic_entry.side_effect = save_synthetic_entry
    port.get_unprocessed_validated_entries.side_effect = get_unprocessed_validated_entries
    port.mark_entries_as_processed.side_effect = mark_entries_as_processed
    return port

@pytest.fixture
def mock_inference():
    engine = MagicMock()
    engine.generate.return_value = "0.9" # AI Score
    return engine

@pytest.fixture
def mock_neo4j():
    return MagicMock()

def test_domain_synthesizer_staging(mock_gold_port, mock_inference, mock_neo4j):
    """Vérifie que le synthétiseur met en attente (stage) au lieu de persister directement."""
    # Mock pour l'évaluation (pour éviter l'erreur de comparaison avec MagicMock)
    mock_neo4j.execute_query.return_value = [{"likes": 10}]
    
    synthesizer = AutonomousDomainSynthesizer(
        inference_engine=mock_inference,
        neo4j_manager=mock_neo4j,
        gold_dataset_port=mock_gold_port
    )
    
    universe = {
        "name": "Test Universe",
        "genre": "Sci-Fi",
        "description": "A test universe description."
    }
    
    # Act
    success = synthesizer.persist_universe_to_graph(universe)
    
    # Assert
    assert success is True
    
    # On vérifie qu'aucune requête de type 'MERGE' (persistance) n'a été envoyée
    for call in mock_neo4j.execute_query.call_args_list:
        query = call.args[0]
        assert "MERGE (m:Media" not in query
        assert "MERGE (c:Character" not in query

    # Gold Port doit avoir reçu une entrée
    assert len(mock_gold_port.entries) == 1
    assert mock_gold_port.entries[0]["entry_type"] == "MULTIVERSE"
    assert mock_gold_port.entries[0]["metadata"]["name"] == "Test Universe"

def test_distillation_pipeline_staging(mock_gold_port, mock_inference):
    """Vérifie que la distillation met en attente (stage) ses données."""
    pipeline = ModelDistillationPipeline(
        teacher_engine=mock_inference,
        prompt_manager=MagicMock(),
        gold_dataset_port=mock_gold_port
    )
    
    pipeline.prompt_manager.get_prompt.return_value = ("prompt", "system")
    mock_inference.generate.return_value = "Explication synthétique."
    
    # Act
    count = pipeline.generate_distillation_data(topics=["Naruto Lore"])
    
    # Assert
    assert count == 1
    assert len(mock_gold_port.entries) == 1
    assert mock_gold_port.entries[0]["entry_type"] == "DISTILLATION"
    assert "Naruto Lore" in mock_gold_port.entries[0]["context"]

def test_promotion_service_execution(mock_gold_port, mock_neo4j):
    """Vérifie que le service de promotion déclenche la persistance réelle après validation."""
    # Setup: On a une entrée MULTIVERSE non validée
    universe_data = {"name": "Valid Universe", "genre": "Shonen", "description": "Desc", "cosmology": "Cosmo", "characters": []}
    mock_gold_port.save_synthetic_entry("MULTIVERSE", "Context", "Instr", "Resp", universe_data)
    
    # On la valide manuellement
    mock_gold_port.entries[0]["is_validated"] = True
    
    # On injecte les mocks dans le promotion service
    mock_synthesizer = AutonomousDomainSynthesizer(neo4j_manager=mock_neo4j)
    promotion_service = SyntheticDataPromotionService(
        gold_dataset_port=mock_gold_port,
        domain_synthesizer=mock_synthesizer
    )
    
    # Act
    result = promotion_service.promote_validated_entries()
    
    # Assert
    assert result["promoted"] == 1
    assert result["details"]["MULTIVERSE"] == 1
    # Neo4j doit avoir été appelé cette fois
    assert mock_neo4j.execute_query.called is True
    # L'entrée doit être retirée du port après promotion (simulé par mark_entries_as_processed)
    assert len(mock_gold_port.entries) == 0
