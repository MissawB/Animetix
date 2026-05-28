import os
import json
import argparse
from animetix.containers import get_container
from core.domain.services.ragas_eval_service import RagasEvalService

def run_mlops_eval():
    """
    Lance une évaluation automatique de la qualité de l'IA sur un échantillon de requêtes.
    Retourne un dictionnaire de stats pour le pipeline MLOps.
    """
    print("🧪 Starting Automated RAG Evaluation (RAGAS)...")
    
    container = get_container()
    judge = container.inference_engine()
    eval_service = RagasEvalService(judge_engine=judge)
    
    # Échantillon de test (Golden Dataset simplifié)
    test_queries = [
        {"q": "Qui est le créateur de One Piece ?", "type": "Anime", "ctx": "Eiichiro Oda"},
        {"q": "Quelle est l'intrigue de Akira ?", "type": "Movie", "ctx": "Katsuhiro Otomo, néo-tokyo"}
    ]
    
    all_scores = []
    
    for item in test_queries:
        print(f"🧐 Evaluating query: '{item['q']}'")
        
        # 1. Génération de la réponse
        response = animetix.agentic_rag.plan_and_solve(item['q'], item['type'])
        
        # 2. Évaluation
        scores = eval_service.evaluate_response(item['q'], item['ctx'], response)
        all_scores.append({"query": item['q'], "scores": scores})
        
    # Stats Finales
    avg_faith = sum(s['scores']['faithfulness'] for s in all_scores) / len(all_scores)
    avg_relevancy = sum(s['scores']['answer_relevancy'] for s in all_scores) / len(all_scores)
    
    report = {
        "avg_faithfulness": avg_faith,
        "avg_answer_relevancy": avg_relevancy,
        "timestamp": str(datetime.now())
    }

    print("\n" + "═"*30)
    print(f"📊 MLOPS REPORT")
    print(f"✅ Avg Faithfulness: {avg_faith:.2f}")
    print(f"🎯 Avg Relevancy: {avg_relevancy:.2f}")
    print("═"*30)
    
    return report

if __name__ == "__main__":
    from datetime import datetime
    run_mlops_eval()
