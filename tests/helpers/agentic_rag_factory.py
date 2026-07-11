"""Test factory for :class:`AgenticRAGService`.

This used to live in ``AgenticRAGService.__init__`` as ``isinstance(..., Mock)``
branches so unit tests could pass mock dependencies and still get a runnable state
machine. That test-only logic has been moved here, out of the production service.

``build_test_agentic_rag_service`` reproduces the previous implicit behavior exactly:
- if ``llm_service`` is a Mock, its ``generate``/``generate_structured`` get a default
  side-effect (return the configured ``_mock_return_value`` else delegate to the
  inference engine / raise to fall back to classic generate);
- if ``workflow_orchestrator`` is a Mock (or omitted), a *real* ``RAGOrchestrator``
  populated with real agents is built from the (mock) dependencies; a real
  orchestrator passed explicitly is used as-is.
"""

from typing import cast
from unittest.mock import DEFAULT, MagicMock, Mock

from core.domain.entities.ai_schemas import RAGState
from core.domain.services.agentic_rag_service import AgenticRAGService
from core.domain.services.xai_service import XaiDiagnosticService
from core.ports.graph_persistence_port import GraphPersistencePort


def _wire_mock_async_stream(mock_obj):
    """Give a Mock a real ``astream_generate`` bridging its ``stream_generate``.

    The RAG pipeline is async-only: real adapters inherit InferencePort's
    default thread-bridge, but bare MagicMocks auto-answer ``__aiter__`` with
    an empty stream, silently dropping the tokens tests configured on the sync
    ``stream_generate``. The bridge reads ``stream_generate`` at call time, so
    tests may configure it after building the service, exactly as before.
    """
    if not isinstance(mock_obj, Mock):
        return

    async def _astream(*args, **kwargs):
        for chunk in mock_obj.stream_generate(*args, **kwargs):
            yield chunk

    mock_obj.astream_generate = _astream


def _wire_mock_llm_fallback(llm_service, inference_engine):
    """Block A: give a mock llm_service sensible default generate behavior."""
    if not isinstance(llm_service, Mock):
        return

    def default_generate(*args, **kwargs):
        ret = llm_service.generate._mock_return_value
        if ret is not DEFAULT:
            return ret
        return inference_engine.generate(*args, **kwargs)

    def default_generate_structured(*args, **kwargs):
        ret = llm_service.generate_structured._mock_return_value
        if ret is not DEFAULT:
            return ret
        raise Exception("Fallback to classic generate for tests")

    if getattr(llm_service.generate, "side_effect", None) is None:
        llm_service.generate.side_effect = default_generate
    if getattr(llm_service.generate_structured, "side_effect", None) is None:
        llm_service.generate_structured.side_effect = default_generate_structured


def _build_real_orchestrator(
    *,
    llm_service,
    prompt_manager,
    neo4j_manager,
    web_search,
    rag_service,
    inference_engine,
    xai_service,
):
    """Block B: build a real RAGOrchestrator with real agents from (mock) deps."""
    from core.domain.services.rag.agents import (
        ContextCompressor,
        GraphExpert,
        LibrarianAgent,
        ResponseCritic,
        ResponseJudge,
        ResponseSynthesizer,
        RetrievalEvaluator,
        ScoutAgent,
        SearchPlanner,
    )
    from core.domain.services.rag.agents.debate_manager import DebateManager
    from core.domain.services.rag.agents.forge import ForgeAgent
    from core.domain.services.rag.agents.saga_agent import SagaAgent
    from core.domain.services.rag.processors.acquire_knowledge_processor import (
        AcquireKnowledgeProcessor,
    )
    from core.domain.services.rag.processors.fallback_rag_processor import (
        FallbackRagProcessor,
    )
    from core.domain.services.rag.processors.graph_explore_processor import (
        GraphExploreProcessor,
    )
    from core.domain.services.rag.processors.judge_processor import JudgeProcessor
    from core.domain.services.rag.processors.plan_processor import PlanProcessor
    from core.domain.services.rag.processors.research_processor import ResearchProcessor
    from core.domain.services.rag.processors.saga_lookup_processor import (
        SagaLookupProcessor,
    )
    from core.domain.services.rag.processors.speculate_processor import (
        SpeculateProcessor,
    )
    from core.domain.services.rag.processors.synthesize_processor import (
        SynthesizeProcessor,
    )
    from core.domain.services.rag.processors.vlm_rerank_processor import (
        VlmRerankProcessor,
    )
    from core.domain.services.rag_orchestrator import RAGOrchestrator

    planner_agent = SearchPlanner(llm_service, prompt_manager)
    scout_agent = ScoutAgent(llm_service, prompt_manager, neo4j_manager)
    synthesizer_agent = ResponseSynthesizer(llm_service, prompt_manager)
    ResponseJudge(llm_service, prompt_manager)
    ResponseCritic(llm_service, prompt_manager)
    debate_mgr = DebateManager(llm_service, prompt_manager)
    librarian_agent = LibrarianAgent(llm_service, prompt_manager, web_search)
    # ForgeAgent/SagaAgent tolerate a missing graph manager at runtime (they guard
    # ``self.neo4j_manager`` before use), but their __init__ signatures require a
    # non-None port. In the test path the port may legitimately be None.
    forge_agent = ForgeAgent(
        llm_service, prompt_manager, cast(GraphPersistencePort, neo4j_manager)
    )
    saga_agent = SagaAgent(llm_service, cast(GraphPersistencePort, neo4j_manager))
    graph_expert = GraphExpert(llm_service, prompt_manager)
    context_compressor = ContextCompressor(llm_service, prompt_manager)
    retrieval_evaluator = RetrievalEvaluator(llm_service, prompt_manager)

    processors = {
        RAGState.PLAN: PlanProcessor(planner=planner_agent),
        RAGState.SAGA_LOOKUP: SagaLookupProcessor(saga_agent=saga_agent),
        RAGState.GRAPH_EXPLORE: GraphExploreProcessor(
            community_partitioner=MagicMock(),
            graph_expert=graph_expert,
            neo4j_manager=neo4j_manager,
        ),
        RAGState.RESEARCH: ResearchProcessor(
            planner=planner_agent,
            rag_service=rag_service,
            context_compressor=context_compressor,
            retrieval_evaluator=retrieval_evaluator,
            web_search=web_search,
            scout=scout_agent,
            neo4j_manager=neo4j_manager,
        ),
        RAGState.ACQUIRE_KNOWLEDGE: AcquireKnowledgeProcessor(
            librarian=librarian_agent
        ),
        RAGState.SPECULATE: SpeculateProcessor(forge=forge_agent),
        RAGState.VLM_RERANK: VlmRerankProcessor(
            inference_engine=inference_engine, prompt_manager=prompt_manager
        ),
        RAGState.SYNTHESIZE: SynthesizeProcessor(
            synthesizer=synthesizer_agent, xai_service=xai_service
        ),
        RAGState.JUDGE: JudgeProcessor(debate_manager=debate_mgr),
        RAGState.FALLBACK_RAG: FallbackRagProcessor(
            rag_service=rag_service,
            inference_engine=inference_engine,
            expert_facts=[],
        ),
    }
    return RAGOrchestrator(processors=processors)


def build_test_agentic_rag_service(**kwargs) -> AgenticRAGService:
    """Build an AgenticRAGService for unit tests with the previous implicit mock wiring.

    Accepts the same kwargs as ``AgenticRAGService``; resolves missing core deps to
    ``MagicMock``, wires the mock-llm fallback, and rebuilds a real orchestrator when
    a Mock one is supplied. Pass a real ``workflow_orchestrator`` to keep it untouched.
    """
    inference_engine = kwargs.setdefault("inference_engine", MagicMock())
    rag_service = kwargs.setdefault("rag_service", MagicMock())
    web_search = kwargs.setdefault("web_search", MagicMock())
    prompt_manager = kwargs.setdefault("prompt_manager", MagicMock())
    llm_service = kwargs.setdefault("llm_service", MagicMock())
    kwargs.setdefault("workflow_orchestrator", MagicMock())
    neo4j_manager = kwargs.get("neo4j_manager")
    xai_service = (
        kwargs.get("xai_service")
        or kwargs.get("uncertainty_service")
        or XaiDiagnosticService(inference_engine)
    )

    _wire_mock_llm_fallback(llm_service, inference_engine)
    _wire_mock_async_stream(llm_service)
    _wire_mock_async_stream(inference_engine)

    if isinstance(kwargs["workflow_orchestrator"], Mock):
        kwargs["workflow_orchestrator"] = _build_real_orchestrator(
            llm_service=llm_service,
            prompt_manager=prompt_manager,
            neo4j_manager=neo4j_manager,
            web_search=web_search,
            rag_service=rag_service,
            inference_engine=inference_engine,
            xai_service=xai_service,
        )

    return AgenticRAGService(**kwargs)
