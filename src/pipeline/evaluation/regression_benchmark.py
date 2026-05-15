import os
import json
import time
from typing import List, Dict
import torch
from animetix.containers import get_container

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- GOLD SET DE RÉFÉRENCE ---
# Ce set contient des questions avec le contexte attendu ou des faits clés.
GOLD_SET = [
    {
        "query": "Qui a produit l'anime Naruto ?",
        "expected_facts": ["Studio Pierrot", "Masashi Kishimoto"],
        "media_type": "Anime"
    },
    {
        "query": "De quoi parle le manga Berserk ?",
        "expected_facts": ["Guts", "Griffith", "Dark Fantasy", "Beherit"],
        "media_type": "Manga"
    },
    {
        "query": "Quelles sont les thématiques de Cowboy Bebop ?",
        "expected_facts": ["Espace", "Chasseurs de primes", "Jazz", "Passé"],
        "media_type": "Anime"
    }
]

def run_regression_test(model_adapter=None):
    """
    Exécute un benchmark de précision et performance sur l'Oracle.
    Permet de comparer les formats (GGUF vs FP16) ou les modèles (Qwen vs Llama).
    """
    print(f"🧪 Starting AI Regression Test...")
    container = get_container()
    agent = container.agentic_rag
    
    # Si un adaptateur spécifique est passé, on l'injecte temporairement
    if model_adapter:
        agent.inference_engine = model_adapter

    results = []
    total_score = 0

    for test in GOLD_SET:
        print(f"   🤔 Testing: '{test['query']}'...")
        start_time = time.time()
        
        # On exécute le RAG Agentique (mode non-streaming pour le test)
        answer = agent.plan_and_solve(test['query'], test['media_type'])
        latency = time.time() - start_time
        
        # Scoring simple : présence des faits attendus
        hits = 0
        for fact in test['expected_facts']:
            if fact.lower() in answer.lower():
                hits += 1
        
        accuracy = hits / len(test['expected_facts'])
        total_score += accuracy
        
        results.append({
            "query": test['query'],
            "accuracy": accuracy,
            "latency": latency,
            "hits": hits,
            "total_facts": len(test['expected_facts'])
        })

    avg_accuracy = total_score / len(GOLD_SET)
    avg_latency = sum(r['latency'] for r in results) / len(results)

    report = {
        "timestamp": time.time(),
        "model_id": getattr(agent.inference_engine, 'model_path', 'unknown'),
        "avg_accuracy": avg_accuracy,
        "avg_latency": avg_latency,
        "details": results
    }

    # Sauvegarde du rapport pour comparaison historique
    report_path = os.path.join(BASE_DIR, 'data', 'mlops', f"regression_report_{int(time.time())}.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ Regression Test Complete.")
    print(f"📊 Avg Accuracy: {avg_accuracy:.2%}")
    print(f"⏱️ Avg Latency: {avg_latency:.2f}s")
    
    return report

if __name__ == "__main__":
    run_regression_test()
