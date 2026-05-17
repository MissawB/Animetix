
import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.agentic_rag_service import AgenticRAGService, RAGState, RAGContext
from core.domain.entities.ai_schemas import SearchPlan, JudgeEvaluation, JudgeAction, StreamStep

@pytest.fixture
def mock_deps():
    return {
        'inference_engine': MagicMock(),
        'rag_service': MagicMock(),
        'web_search': MagicMock(),
        'prompt_manager': MagicMock(),
        'llm_service': MagicMock(),
        'obs_service': MagicMock()
    }

def test_research_more_loop_integration(mock_deps):
    """
    Vérifie que la machine à états peut boucler de JUDGE vers RESEARCH
    quand le Judge demande plus de recherche, puis finit par APPROVE.
    """
    # Initialisation du service
    service = AgenticRAGService(**mock_deps)
    
    # Mock des agents internes pour contrôler finement les transitions
    service.planner = MagicMock()
    service.scout = MagicMock()
    service.synthesizer = MagicMock()
    service.judge = MagicMock()
    
    # Mock des méthodes utilitaires
    service._assess_complexity = MagicMock(return_value=(0, 0))
    service._get_memories = MagicMock(return_value="")
    service._execute_search = MagicMock(return_value="raw_results")
    
    # --- CONFIGURATION DU SCÉNARIO ---
    
    # 1. Planner retourne un plan simple
    service.planner.plan.return_value = SearchPlan(optimized_query="test query", requires_web=False)
    
    # 2. Scout retourne un chemin de vérité
    service.scout.find_truth_path.return_value = "truth_path"
    
    # 3. Synthesizer simule un stream de tokens
    service.synthesizer.synthesize_stream.return_value = iter(["Réponse", " finale"])
    
    # 4. Judge simule : RESEARCH_MORE au premier tour, puis APPROVE au second
    service.judge.evaluate.side_effect = [
        JudgeEvaluation(
            faithfulness_score=0.5,
            relevancy_score=0.5,
            hallucination_detected=False,
            reasoning="Il manque des détails sur X.",
            is_reliable=False,
            next_action=JudgeAction.RESEARCH_MORE
        ),
        JudgeEvaluation(
            faithfulness_score=1.0,
            relevancy_score=1.0,
            hallucination_detected=False,
            reasoning="Parfait maintenant.",
            is_reliable=True,
            next_action=JudgeAction.APPROVE
        )
    ]
    
    # On augmente max_iterations pour être sûr que ça passe (PLAN(1) + RES(2) + SYN(3) + JUD(4) + RES(5) + SYN(6) + JUD(7))
    # Mais wait, AgenticRAGService instancie RAGContext en dur avec max_iterations=5.
    # On va patcher la classe RAGContext pour le test.
    
    with patch('core.domain.services.agentic_rag_service.RAGContext') as MockContext:
        # On définit le comportement du mock pour retourner une instance réelle mais modifiée
        def side_effect_ctx(**kwargs):
            kwargs['max_iterations'] = 10
            return RAGContext(**kwargs)
        MockContext.side_effect = side_effect_ctx
        
        # Exécution du stream
        events = list(service.plan_and_solve_stream("Quelle est la capitale de la France ?", "Anime"))
    
    # --- VÉRIFICATIONS ---
    
    # Extraire les transitions d'état depuis les logs de pensée
    state_logs = [e['content'] for e in events if e['type'] == 'thought' and "[State Machine]" in e['content']]
    
    # Vérification de l'ordre des états
    expected_sequence = [
        "État: RAGState.PLAN",
        "État: RAGState.RESEARCH",
        "État: RAGState.SYNTHESIZE",
        "État: RAGState.JUDGE",
        "État: RAGState.RESEARCH", # Deuxième boucle suite à RESEARCH_MORE
        "État: RAGState.SYNTHESIZE",
        "État: RAGState.JUDGE"
    ]
    
    for i, expected in enumerate(expected_sequence):
        assert expected in state_logs[i], f"Séquence incorrecte à l'index {i}. Attendu: {expected}, Reçu: {state_logs[i]}"
        
    # Vérification des appels
    assert service.planner.plan.call_count == 1
    assert service.scout.find_truth_path.call_count == 2
    assert service.synthesizer.synthesize_stream.call_count == 2
    assert service.judge.evaluate.call_count == 2
    
    # Vérification de la réponse finale concaténée
    tokens = [e['content'] for e in events if e['type'] == 'token']
    assert "".join(tokens) == "Réponse finale"

def test_rewrite_loop(mock_deps):
    """Vérifie que REWRITE ramène bien à SYNTHESIZE."""
    service = AgenticRAGService(**mock_deps)
    service.planner = MagicMock()
    service.scout = MagicMock()
    service.synthesizer = MagicMock()
    service.judge = MagicMock()
    service._assess_complexity = MagicMock(return_value=(0, 0))
    service._execute_search = MagicMock(return_value="raw")

    service.planner.plan.return_value = SearchPlan(optimized_query="test", requires_web=False)
    service.scout.find_truth_path.return_value = "truth"
    service.synthesizer.synthesize_stream.return_value = iter(["Fix"])
    
    service.judge.evaluate.side_effect = [
        JudgeEvaluation(
            faithfulness_score=0.8, relevancy_score=1.0, hallucination_detected=False,
            reasoning="Style incorrect", is_reliable=False, next_action=JudgeAction.REWRITE
        ),
        JudgeEvaluation(
            faithfulness_score=1.0, relevancy_score=1.0, hallucination_detected=False,
            reasoning="Ok", is_reliable=True, next_action=JudgeAction.APPROVE
        )
    ]
    
    events = list(service.plan_and_solve_stream("query", "Anime"))
    state_logs = [e['content'] for e in events if e['type'] == 'thought' and "[State Machine]" in e['content']]
    
    # PLAN -> RESEARCH -> SYNTHESIZE -> JUDGE -> SYNTHESIZE -> JUDGE
    expected = ["PLAN", "RESEARCH", "SYNTHESIZE", "JUDGE", "SYNTHESIZE", "JUDGE"]
    for i, state in enumerate(expected):
        assert state in state_logs[i]
