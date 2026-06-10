import os
import sys
from unittest.mock import MagicMock

# Ajout des chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "api"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.animetix_project.settings')
import django
try:
    django.setup()
except Exception as e:
    pass

from core.domain.services.agentic_rag_service import AgenticRAGService
from core.domain.services.xai_service import XaiDiagnosticService
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata, TokenLogProb

def mock_get_diagnostics(prompt, completion):
    return {
        "attention_heatmap": [[0.1, 0.9], [0.8, 0.2]],
        "top_attention_tokens": ["Nen", "Aura", "Hunter"],
        "logit_lens": [
            {"layer": "Layer_0", "top_token": "Le", "confidence": 0.9},
            {"layer": "Layer_12", "top_token": "Nen", "confidence": 0.85}
        ]
    }

def main():
    print("🚀 Initialisation de AgenticRAGService (Mocked)...")
    
    # Mocking dependencies
    mock_engine = MagicMock()
    # We no longer mock get_diagnostics and calculate_uncertainty since we rely on native logprobs
    
    logprobs_data = [
        TokenLogProb(token="Le", logprob=-0.05, top_logprobs=[{"Le": -0.05}]),
        TokenLogProb(token=" Nen", logprob=-0.1, top_logprobs=[{" Nen": -0.1}]),
        TokenLogProb(token=" est", logprob=-0.02, top_logprobs=[{" est": -0.02}]),
        TokenLogProb(token=" l'énergie", logprob=-0.08, top_logprobs=[{" l'énergie": -0.08}]),
    ]
    
    mock_engine.stream_generate.return_value = [
        InferenceResponse(text="Le ", metadata=InferenceMetadata(logprobs=[logprobs_data[0]])),
        InferenceResponse(text="Nen ", metadata=InferenceMetadata(logprobs=[logprobs_data[1]])),
        InferenceResponse(text="est ", metadata=InferenceMetadata(logprobs=[logprobs_data[2]])),
        InferenceResponse(text="l'énergie ", metadata=InferenceMetadata(logprobs=[logprobs_data[3]])),
        InferenceResponse(text="vitale.", metadata=InferenceMetadata(logprobs=[]))
    ]
    
    mock_workflow = MagicMock()
    
    mock_memory = MagicMock()
    mock_memory.retrieve_relevant_memories.return_value = "Mémoires de test."
    
    mock_neo4j = MagicMock()
    mock_neo4j.get_user_preferences_context.return_value = "Contexte graphe de test."
    
    # Initialize unified XAI service
    xai_service = XaiDiagnosticService(mock_engine)
    
    mock_cache = MagicMock()
    mock_cache.get_cached_response.return_value = None
    
    mock_router = MagicMock()
    mock_router.classify.return_value = "COMPLEX"
    
    # Initialize AgenticRAGService
    agentic_rag = AgenticRAGService(
        inference_engine=mock_engine,
        rag_service=MagicMock(),
        web_search=MagicMock(),
        prompt_manager=MagicMock(),
        llm_service=MagicMock(),
        workflow_manager=mock_workflow,
        neo4j_manager=mock_neo4j,
        memory_service=mock_memory,
        semantic_cache=mock_cache,
        obs_service=MagicMock(),
        xai_service=xai_service,
        semantic_router=mock_router
    )
    
    # Mock workflow manager to go straight to synthesize and finalize
    def mock_run_workflow(ctx, xai_collector=None):
        ctx.current_state = "SYNTHESIZE"
        if xai_collector:
            xai_collector.log_intent("Expliquer le Nen")
            xai_collector.log_retrieval([{"id": "doc1", "title": "Wiki Nen", "score": 0.95}])
            xai_collector.log_agent_thought("Planner", "Recherche d'informations basiques sur le Nen.")
        
        ctx.full_answer = "Le Nen est l'énergie vitale."
        yield {"type": "token", "content": "Le "}
        yield {"type": "token", "content": "Nen "}
        yield {"type": "thought", "content": "[Synthesizer] Rédaction en cours..."}
        
        ctx.current_state = "FINALIZE"
        
    agentic_rag.workflow_manager.run_workflow = mock_run_workflow
    
    query = "Explique moi le concept de Nen dans Hunter x Hunter. (TEST XAI UNIQUE 12345)"
    print(f"\n🧠 Requête : {query}\n")
    
    try:
        for step in agentic_rag.plan_and_solve_stream(query=query, media_type="anime", user_id="test_user"):
            step_type = step.get('type')
            if step_type == 'xai_report':
                print("\n\n" + "="*60)
                print("📊 RAPPORT XAI (EXPLAINABLE AI) GÉNÉRÉ :")
                print("="*60)
                import json
                print(json.dumps(step.get('content'), indent=2, ensure_ascii=False))
                print("="*60 + "\n")
            elif step_type == 'thought':
                print(f"💭 {step.get('content')}")
            elif step_type == 'token':
                print(step.get('content'), end="", flush=True)
    except Exception as e:
        print(f"\n❌ Erreur pendant le stream: {e}")

if __name__ == "__main__":
    main()