import pytest
from unittest.mock import MagicMock
from core.domain.services.agentic_rag_service import AgenticRAGService
from core.domain.entities.ai_schemas import StreamStep, RAGContext, SearchPlan

def test_chronicler_theories_integration():
    # Setup mocks
    mock_llm = MagicMock()
    mock_neo4j = MagicMock()
    mock_web_search = MagicMock()
    mock_prompt_mgr = MagicMock()
    mock_inference = MagicMock()
    mock_rag_service = MagicMock()

    # Chronicler Agent pulse community - mock the method
    # Since it is called by ChroniclerAgent.pulse_community and AgenticRAGService uses it, 
    # we need to ensure the RAG service uses the mocked components.
    
    rag_service = AgenticRAGService(
        inference_engine=mock_inference,
        rag_service=mock_rag_service,
        web_search=mock_web_search,
        prompt_manager=mock_prompt_mgr,
        llm_service=mock_llm,
        workflow_orchestrator=MagicMock(),
        neo4j_manager=mock_neo4j
    )

    # Mock the theory data in Neo4j
    mock_neo4j.execute_read.return_value = [
        {"title": "Imu is JoyBoy", "desc": "Imu is actually JoyBoy from the past.", "plausibility": 0.8}
    ]

    # Run the query
    query = "Quelle est la théorie sur Imu ?"
    
    # We are testing the theory detection logic inside ResearchProcessor.
    ctx = RAGContext(query=query, media_type="Anime")
    ctx.plan = SearchPlan(optimized_query="Imu theory", entities=["Imu"], reasoning="Test planning")

    # Directly trigger ResearchProcessor.process
    from backend.core.domain.services.rag.processors.research_processor import ResearchProcessor
    processor = ResearchProcessor(
        planner=MagicMock(),
        rag_service=mock_rag_service,
        context_compressor=MagicMock(),
        retrieval_evaluator=MagicMock(),
        web_search=mock_web_search,
        video_rag_service=MagicMock(),
        scout=MagicMock(),
        neo4j_manager=mock_neo4j
    )
    gen = processor.process(ctx)
    
    events = list(gen)
    
    # Assertions
    assert any("CONSENSUS DE FANS (THÉORIES)" in ctx.truth_path for _ in [0])
    assert "Imu is JoyBoy" in ctx.truth_path
    assert "Imu is actually JoyBoy from the past." in ctx.truth_path
    assert any(e['content'] == "[Chronicler] Vérification des théories de fans dans la base..." for e in events)

    print("\nTest passed: Theory found and added to RAGContext.")
