import os
import json
import time
from typing import List, Dict
import torch
from animetix.containers import get_container

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- GOLD SET DE RÉFÉRENCE ---
# Ce set couvre les différents types de médias et niveaux de complexité.
GOLD_SET = [
    {
        "query": "Explique l'intrigue de l'anime Death Note en une phrase.",
        "expected_facts": ["Light Yagami", ["Ryuk", "dieu de la mort", "shinigami"], ["carnet", "livre", "cahier", "système de notes", "Death Note"]],
        "media_type": "Anime"
    },
    {
        "query": "Qui est l'auteur du manga One Piece ?",
        "expected_facts": [["Eiichiro Oda", "Oda"]],
        "media_type": "Manga"
    },
    {
        "query": "Quelle est l'arme emblématique de Guts dans Berserk ?",
        "expected_facts": [["Dragon Slayer", "Dragonslayer", "épée", "lame géante"]],
        "media_type": "Character"
    },
    {
        "query": "Qui a créé la franchise de jeux vidéo Metal Gear ?",
        "expected_facts": [["Hideo Kojima", "Kojima"]],
        "media_type": "Game"
    },
    {
        "query": "Quel studio a produit l'anime Neon Genesis Evangelion ?",
        "expected_facts": [["Gainax", "Studio Gainax"]],
        "media_type": "Anime"
    },
    {
        "query": "Quel studio est derrière l'animation de Jujutsu Kaisen ?",
        "expected_facts": [["MAPPA", "Studio MAPPA"]],
        "media_type": "Anime"
    },
    {
        "query": "Qui interprète le rôle du Joker dans le film The Dark Knight de 2008 ?",
        "expected_facts": [["Heath Ledger", "Ledger"]],
        "media_type": "Movie"
    },
    {
        "query": "Quelle maison d'édition publie le manga Berserk en France ?",
        "expected_facts": [["Glénat", "Editions Glénat"]],
        "media_type": "Manga"
    },
    {
        "query": "Quel comédien de doublage français prête sa voix principale au personnage de Luffy dans l'anime One Piece ?",
        "expected_facts": [["Stéphane Excoffier", "Excoffier", "Brigitte Lecordier", "Lecordier"]],
        "media_type": "Character"
    },
    {
        "query": "Quel prix prestigieux a récompensé le manga L'Attaque des Titans en 2011 au Japon ?",
        "expected_facts": [["Prix du manga Kōdansha", "Kodansha Manga Award", "Kodansha", "Kōdansha"]],
        "media_type": "Manga"
    },
    {
        "query": "Combien de saisons et d'épisodes compte l'adaptation animée de Demon Slayer (Kimetsu no Yaiba) ?",
        "expected_facts": [["4 saisons", "quatre saisons"], ["60 épisodes", "soixante épisodes"]],
        "media_type": "Anime"
    },
    {
        "query": "Dans quel magazine de prépublication japonais a été sérialisé le manga Hunter x Hunter ?",
        "expected_facts": [["Weekly Shōnen Jump", "Shonen Jump", "Weekly Shonen Jump"]],
        "media_type": "Manga"
    }
]

def run_regression_test(model_adapter=None):
    """Benchmark de précision IA."""
    print(f"🧪 Starting AI Regression Test...")
    container = get_container()
    agent = container.agentic_rag
    
    # DÉSACTIVATION DU CACHE POUR LE TEST
    agent.semantic_cache = None
    
    # Si un adaptateur spécifique est passé, on l'injecte temporairement
    if model_adapter:
        agent.inference_engine = model_adapter

    results = []
    total_score = 0

    for test in GOLD_SET:
        print(f"   🤔 Testing: '{test['query']}'...")
        start_time = time.time()
        
        # On exécute le RAG Agentique (mode non-streaming pour le test)
        raw_answer = agent.plan_and_solve(test['query'], test['media_type'])
        latency = time.time() - start_time
        
        # Nettoyage et extraction JSON si nécessaire
        answer_text = raw_answer
        try:
            # Si c'est du JSON, on extrait le champ 'answer'
            import orjson
            content = raw_answer
            if '```json' in content:
                content = content.split('```json')[-1].split('```')[0].strip()
            
            data = orjson.loads(content)
            if isinstance(data, dict) and 'answer' in data:
                answer_text = data['answer']
        except:
            pass # On garde le texte brut si le parsing échoue
            
        print(f"   🤖 AI Answer: {answer_text[:100]}...")
        
        # Scoring : présence des faits attendus (Case insensitive + Strip)
        hits = 0
        for fact in test['expected_facts']:
            if isinstance(fact, list):
                # Au moins un synonyme doit être présent
                if any(syn.lower().strip() in answer_text.lower() for syn in fact):
                    hits += 1
                else:
                    print(f"      ❌ Missing fact (synonyms): {fact}")
            elif fact.lower().strip() in answer_text.lower():
                hits += 1
            else:
                # Tentative sans strip au cas où
                if fact.lower() in answer_text.lower():
                    hits += 1
                else:
                    print(f"      ❌ Missing fact: '{fact}'")
        
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
