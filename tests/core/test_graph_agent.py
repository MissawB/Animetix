import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.agentic_rag_service import AgenticRAGService, RAGState
from core.domain.entities.ai_schemas import SearchPlan, JudgeEvaluation, JudgeAction

@pytest.fixture
def mock_inference():
    engine = MagicMock()
    # Mocking stream_generate for ResponseSynthesizer
    engine.stream_generate.return_value = iter(["Final ", "answer ", "from ", "graph."])
    return engine

@pytest.fixture
def mock_rag_service():
    rag = MagicMock()
    rag.hybrid_search.return_value = []
    return rag

@pytest.fixture
def mock_web_search():
    web = MagicMock()
    web.search.return_value = []
    return web

@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("prompt", "system")
    return pm

@pytest.fixture
def mock_llm_service():
    llm = MagicMock()
    return llm

@pytest.fixture
def mock_neo4j():
    neo = MagicMock()
    neo.execute_query.return_value = [{"p.name": "Mamoru Miyano"}]
    return neo

@pytest.fixture
def agentic_rag(mock_inference, mock_rag_service, mock_web_search, mock_prompt_manager, mock_llm_service, mock_neo4j):
    service = AgenticRAGService(
        inference_engine=mock_inference,
        rag_service=mock_rag_service,
        web_search=mock_web_search,
        prompt_manager=mock_prompt_manager,
        llm_service=mock_llm_service,
        workflow_manager=MagicMock(),
        neo4j_manager=mock_neo4j
    )
    # Force high confidence to skip recovery and librarian
    service.uncertainty_service = MagicMock()
    service.uncertainty_service.measure_confidence.return_value = 1.0
    return service

def test_graph_exploration_flow(agentic_rag, mock_llm_service, mock_neo4j):
    from core.domain.entities.ai_schemas import SearchPlan, DebateOutcome, JudgeAction
    mock_plan = SearchPlan(
        optimized_query="Voice actor both Ghibli and MAPPA",
        requires_graph=True,
        reasoning="relational query"
    )
    mock_llm_service.generate_structured.return_value = mock_plan

    outcome = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="Perfect", critiques={})
    agentic_rag.debate_manager.conduct_debate = MagicMock(return_value=outcome)

    agentic_rag.semantic_router = MagicMock()
    agentic_rag.semantic_router.classify.return_value = "COMPLEX"

    agentic_rag.workflow_manager.community_partitioner = MagicMock()
    agentic_rag.workflow_manager.community_partitioner.search_communities.return_value = [
        {"name": "MOCK", "summary": "MOCK SUMMARY", "entities": ["Mamoru"]}
    ]

    responses = [
        '{"thinking_budget": 0, "complexity_score": 2}', # 1. TTC
        '{"cypher": "MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN p.name", "explanation": "test"}', # 2. GraphExpert
        '{"faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok", "is_reliable": true, "next_action": "APPROVE"}' # 3. Judge
    ]
    
    mock_llm_service.generate.side_effect = responses
    
    steps = []
    tokens = []
    for step in agentic_rag.plan_and_solve_stream("Voice actor for both Ghibli and MAPPA?", "Anime"):
        print(f"DEBUG STEP: {step}")
        steps.append(step)
        if step['type'] == 'token':
            tokens.append(step['content'])
            
    thoughts = [s['content'] for s in steps if s['type'] == 'thought']
    
    print("\n--- THOUGHTS ---")
    for t in thoughts:
        print(t)
    print("----------------\n")
    
    # Assertions
    assert any("GRAPH_EXPLORE" in t for t in thoughts)
    assert any("[Graph-Agent] Génération d'une requête Cypher" in t for t in thoughts)
    assert any("Exécution Cypher" in t for t in thoughts)
    
    # Verify Neo4j was called
    mock_neo4j.execute_query.assert_called_once()
    
    # Verify final answer
    final_answer = "".join(tokens)
    assert "graph" in final_answer.lower()
    
    # Verify that the last evaluation was APPROVE
    eval_steps = [s['content'] for s in steps if s['type'] == 'eval']
    assert eval_steps[-1]['consensus_action'] == JudgeAction.APPROVE

if __name__ == "__main__":
    import sys
    import os
    # Add src to sys.path if running as script
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    pytest.main([__file__, "-s"])
