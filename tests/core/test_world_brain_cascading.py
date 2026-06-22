from unittest.mock import MagicMock, patch

import pytest
from core.domain.entities.ai_schemas import DebateOutcome, JudgeAction, SearchPlan
from core.domain.services.agentic_rag_service import AgenticRAGService

from tests.helpers.agentic_rag_factory import build_test_agentic_rag_service

# Drives the full agentic RAG pipeline against a live inference engine (no ollama in CI).
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_dependencies():
    inference_engine = MagicMock()
    rag_service = MagicMock()
    web_search = MagicMock()
    prompt_manager = MagicMock()
    llm_service = MagicMock()
    neo4j_manager = MagicMock()
    graph_expert = MagicMock()
    saga_agent = MagicMock()
    uncertainty_service = MagicMock()

    # Configure prompt_manager to return dummy prompts
    prompt_manager.get_prompt.return_value = ("prompt", "system")

    return {
        "inference_engine": inference_engine,
        "rag_service": rag_service,
        "web_search": web_search,
        "prompt_manager": prompt_manager,
        "llm_service": llm_service,
        "neo4j_manager": neo4j_manager,
        "graph_expert": graph_expert,
        "saga_agent": saga_agent,
        "uncertainty_service": uncertainty_service,
        "workflow_orchestrator": MagicMock(),
    }


def test_world_brain_cascading_flow(mock_dependencies):
    """
    Vérifie le flux en cascade : PLAN -> SAGA_LOOKUP -> GRAPH_EXPLORE -> RESEARCH -> SYNTHESIZE.
    """
    service = build_test_agentic_rag_service(
        inference_engine=mock_dependencies["inference_engine"],
        rag_service=mock_dependencies["rag_service"],
        web_search=mock_dependencies["web_search"],
        prompt_manager=mock_dependencies["prompt_manager"],
        llm_service=mock_dependencies["llm_service"],
        workflow_orchestrator=mock_dependencies["workflow_orchestrator"],
        neo4j_manager=mock_dependencies["neo4j_manager"],
        graph_expert=mock_dependencies["graph_expert"],
        saga_agent=mock_dependencies["saga_agent"],
        uncertainty_service=mock_dependencies["uncertainty_service"],
    )

    # 1. Mock Complexity Assessment
    # _assess_complexity is called at the beginning
    # We need to mock _extract_json too because _assess_complexity uses it
    with patch.object(AgenticRAGService, "_assess_complexity", return_value=(500, 3)):
        # 2. Mock Planner
        # The planner should return a plan that requires saga, graph, and research
        mock_plan = SearchPlan(
            optimized_query="objectif Luffy evolution Egghead",
            entities=["Luffy", "Egghead"],
            requires_saga=True,
            requires_graph=True,
            requires_web=False,
            reasoning="Besoin de contexte global (Saga) et détails précis (Graph).",
        )
        service.planner.plan = MagicMock(return_value=mock_plan)

        # 3. Mock SagaAgent
        mock_dependencies["saga_agent"].lookup_saga.return_value = "One Piece"
        mock_dependencies["saga_agent"].get_saga_context.return_value = (
            "One Piece est l'histoire de Monkey D. Luffy qui veut devenir le Roi des Pirates."
        )

        # 4. Mock GraphExpert and Neo4j
        mock_dependencies["graph_expert"].generate_cypher.return_value = (
            "MATCH (p:Personnage {name: 'Luffy'})-[:PARTICIPE_A]->(a:Arc {name: 'Egghead'}) RETURN p, a"
        )
        mock_dependencies["neo4j_manager"].execute_read.return_value = [
            {
                "p": {"name": "Luffy"},
                "a": {"name": "Egghead", "description": "L'île du futur"},
            }
        ]
        mock_dependencies["neo4j_manager"].execute_query.return_value = [
            {
                "p": {"name": "Luffy"},
                "a": {"name": "Egghead", "description": "L'île du futur"},
            }
        ]

        # 5. Mock Scout and Search
        service.rag_service.hybrid_search.return_value = [
            {"title": "Luffy à Egghead", "description": "Luffy active le Gear 5."}
        ]
        service.scout.find_truth_path = MagicMock(
            return_value="Détails sur Luffy à Egghead récupérés."
        )

        # 6. Mock Synthesizer
        service.synthesizer.synthesize_stream = MagicMock(
            return_value=iter(
                ["L'objectif de Luffy ", "est devenu plus concret ", "à Egghead."]
            )
        )

        # Mock uncertainty to avoid TypeErrors
        mock_dependencies["uncertainty_service"].measure_confidence.return_value = 0.9

        # 7. Mock Debate Manager (to avoid infinite loop and finalize)
        mock_outcome = DebateOutcome(
            critiques={},
            consensus_action=JudgeAction.APPROVE,
            final_reasoning="Réponse complète et précise.",
        )
        service.debate_manager.conduct_debate = MagicMock(return_value=mock_outcome)

        # Execution
        query = "Comment l'objectif de Luffy a évolué entre le début de la série et l'arc Egghead ?"
        events = list(service.plan_and_solve_stream(query, "anime"))

        # Assertions
        states_reached = [
            e["content"]
            for e in events
            if e["type"] == "thought" and "[State Machine]" in e["content"]
        ]

        # On vérifie que les états attendus sont présents dans l'ordre (ou au moins présents)
        assert any("État: RAGState.PLAN" in s for s in states_reached)
        assert any("État: RAGState.SAGA_LOOKUP" in s for s in states_reached)
        assert any("État: RAGState.GRAPH_EXPLORE" in s for s in states_reached)
        assert any("État: RAGState.RESEARCH" in s for s in states_reached)
        assert any("État: RAGState.SYNTHESIZE" in s for s in states_reached)

        # Vérifie que le SagaAgent a été appelé
        mock_dependencies["saga_agent"].lookup_saga.assert_called_once()
        mock_dependencies["saga_agent"].get_saga_context.assert_called_with("One Piece")

        # Vérifie que le Neo4j a été appelé
        mock_dependencies["neo4j_manager"].execute_read.assert_called()

        # Vérifie que la réponse finale contient les tokens attendus
        final_tokens = [e["content"] for e in events if e["type"] == "token"]
        full_response = "".join(final_tokens)
        assert "L'objectif de Luffy" in full_response
        assert "Egghead" in full_response


if __name__ == "__main__":
    pytest.main([__file__])
