import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.agentic_rag_service import AgenticRAGService, RAGState
from core.domain.services.rag.agents.debate_manager import DebateManager
from core.domain.entities.ai_schemas import (
    JudgeAction, JudgeEvaluation, DebateOutcome, SearchPlan
)
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from core.domain.services.advanced_rag_service import AdvancedRAGService
from core.domain.services.prompt_manager import PromptManager
from core.domain.services.llm_service import LLMService

class TestMultiAgentDebateIntegration:

    @pytest.fixture
    def mock_inference(self):
        return MagicMock(spec=InferencePort)

    @pytest.fixture
    def mock_rag_service(self):
        return MagicMock(spec=AdvancedRAGService)

    @pytest.fixture
    def mock_web_search(self):
        return MagicMock(spec=WebSearchPort)

    @pytest.fixture
    def mock_prompt_manager(self):
        pm = MagicMock(spec=PromptManager)
        # Mocking complexity assessment
        pm.get_prompt.side_effect = lambda key, **kwargs: (f"Prompt for {key}", "System prompt")
        return pm

    @pytest.fixture
    def mock_llm_service(self):
        return MagicMock(spec=LLMService)

    def test_debate_consensus_rewrite(self, mock_inference, mock_rag_service, mock_web_search, mock_prompt_manager, mock_llm_service):
        """
        Tests that when judges return conflicting evaluations, 
        DebateManager correctly identifies the consensus as REWRITE
        and AgenticRAGService transitions back to SYNTHESIZE.
        """
        # 1. Setup mocks for judge evaluations
        # We'll mock LLMService.generate to return JSON strings for each judge
        # judge_lore_expert: APPROVE
        # judge_logic_auditor: REWRITE
        # judge_critic: APPROVE
        
        lore_eval = JudgeEvaluation(
            faithfulness_score=0.9,
            relevancy_score=0.9,
            hallucination_detected=False,
            reasoning="Lore is correct.",
            is_reliable=True,
            next_action=JudgeAction.APPROVE
        )
        logic_eval = JudgeEvaluation(
            faithfulness_score=0.5,
            relevancy_score=0.8,
            hallucination_detected=True,
            reasoning="Logic error detected in the synthesis.",
            is_reliable=False,
            next_action=JudgeAction.REWRITE
        )
        critic_eval = JudgeEvaluation(
            faithfulness_score=0.9,
            relevancy_score=0.9,
            hallucination_detected=False,
            reasoning="Style is good.",
            is_reliable=True,
            next_action=JudgeAction.APPROVE
        )

        def mock_generate(prompt, system_prompt=None, **kwargs):
            if "judge_lore_expert" in prompt:
                return lore_eval.model_dump_json()
            if "judge_logic_auditor" in prompt:
                return logic_eval.model_dump_json()
            if "judge_critic" in prompt:
                return critic_eval.model_dump_json()
            if "complexity_analyzer" in prompt:
                return '{"thinking_budget": 100, "complexity_score": 3}'
            return "{}"

        mock_llm_service.generate.side_effect = mock_generate

        # Mock Planner to skip Graph/Web for simplicity
        planner_mock = MagicMock()
        planner_mock.plan.return_value = SearchPlan(
            optimized_query="test query",
            reasoning="simple plan",
            requires_web=False,
            requires_graph=False
        )

        # Mock Synthesizer
        synthesizer_mock = MagicMock()
        # We need enough items for the number of iterations
        synthesizer_mock.synthesize_stream.side_effect = [
            iter(["First attempt "]), 
            iter(["Second corrected attempt "]),
            iter(["Third attempt "])
        ]

        service = AgenticRAGService(
            inference_engine=mock_inference,
            rag_service=mock_rag_service,
            web_search=mock_web_search,
            prompt_manager=mock_prompt_manager,
            llm_service=mock_llm_service,
            workflow_manager=MagicMock()
        )
        service.uncertainty_service = MagicMock()
        service.uncertainty_service.measure_confidence.return_value = {"confidence_score": 1.0, "is_reliable": True}
        service.planner = planner_mock
        service.synthesizer = synthesizer_mock

        # Setup dynamic mock for LLM generate
        call_count = {"judge_logic_auditor": 0}
        def mock_generate_dynamic(prompt, system_prompt=None, **kwargs):
            if "judge_lore_expert" in prompt: return lore_eval.model_dump_json()
            if "judge_critic" in prompt: return critic_eval.model_dump_json()
            if "judge_logic_auditor" in prompt:
                call_count["judge_logic_auditor"] += 1
                if call_count["judge_logic_auditor"] == 1:
                    return logic_eval.model_dump_json()
                else:
                    return lore_eval.model_dump_json() # Return APPROVE the second time
            if "complexity_analyzer" in prompt:
                return '{"thinking_budget": 100, "complexity_score": 3}'
            return "{}"
        
        mock_llm_service.generate.side_effect = mock_generate_dynamic

        # Run the stream ONCE with the dynamic mock
        events = list(service.plan_and_solve_stream("Who is Goku?", "anime"))

        # 2. Verifications
        
        # Check if JUDGE state was reached
        judge_states = [e for e in events if e['type'] == 'thought' and "État: RAGState.JUDGE" in e['content']]
        assert len(judge_states) >= 2, f"Should have reached JUDGE state at least twice. Events: {events}"

        # Check for REWRITE consensus
        rewrite_consensus = [e for e in events if e['type'] == 'thought' and "Consensus : JudgeAction.REWRITE" in e['content']]
        assert len(rewrite_consensus) == 1, f"Should have a REWRITE consensus once. Events: {events}"

        # Check for APPROVE consensus
        approve_consensus = [e for e in events if e['type'] == 'thought' and "Consensus : JudgeAction.APPROVE" in e['content']]
        assert len(approve_consensus) == 1, f"Should have an APPROVE consensus once. Events: {events}"

        # Check if eval event contains DebateOutcome
        eval_events = [e for e in events if e['type'] == 'eval']
        assert len(eval_events) >= 2
        
        first_eval = eval_events[0]['content']
        assert first_eval['consensus_action'] == JudgeAction.REWRITE
        assert "judge_logic_auditor" in first_eval['critiques']
        
        second_eval = eval_events[1]['content']
        assert second_eval['consensus_action'] == JudgeAction.APPROVE

        # Verify that synth was called twice
        assert synthesizer_mock.synthesize_stream.call_count == 2
