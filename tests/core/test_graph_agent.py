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
    return AgenticRAGService(
        inference_engine=mock_inference,
        rag_service=mock_rag_service,
        web_search=mock_web_search,
        prompt_manager=mock_prompt_manager,
        llm_service=mock_llm_service,
        neo4j_manager=mock_neo4j
    )

def test_graph_exploration_flow(agentic_rag, mock_llm_service, mock_neo4j):
    # side_effect for LLMService.generate
    # 1. Complexity Analyzer
    # 2. Planner (requires_graph=True)
    # 3. GraphExpert (Cypher generation)
    # 4. Judge (Approval) - Scout is skipped because raw_context is empty
    
    responses = [
        '{"thinking_budget": 0, "complexity_score": 2}', # 1. TTC
        '{"optimized_query": "Voice actor both Ghibli and MAPPA", "requires_graph": true, "reasoning": "relational query"}', # 2. Planner
        '{"cypher": "MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN p.name", "explanation": "test"}', # 3. GraphExpert
        '{"faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok", "is_reliable": true, "next_action": "APPROVE"}' # 4. Judge
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
    assert eval_steps[-1]['next_action'] == JudgeAction.APPROVE

if __name__ == "__main__":
    import sys
    import os
    # Add src to sys.path if running as script
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    pytest.main([__file__, "-s"])
