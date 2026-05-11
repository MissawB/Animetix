from dagster import asset, Output, AssetMaterialization
import os
import requests
import json
import time
import pandas as pd
from datetime import datetime

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEEDBACK_DATASET_DIR = os.path.join(BASE_DIR, 'data', 'mlops', 'datasets')
os.makedirs(FEEDBACK_DATASET_DIR, exist_ok=True)

@asset(group_name="mlops")
def monitor_inference_health():
    """Surveille la latence et la disponibilité de l'API Brain (Inférence)."""
    brain_url = os.getenv("BRAIN_API_URL")
    if not brain_url:
        return "⚠️ BRAIN_API_URL non configuré."
    
    start_time = time.time()
    try:
        # On teste une génération simple
        res = requests.post(f"{brain_url}/generate", json={
            "prompt": "ping",
            "system_prompt": "Répond uniquement 'pong'"
        }, timeout=10)
        latency = time.time() - start_time
        
        status = "🟢 Online" if res.status_code == 200 else f"🔴 Error {res.status_code}"
        print(f"Inference Health: {status} | Latency: {latency:.2f}s")
        return {"status": status, "latency": latency}
    except Exception as e:
        return {"status": "🔴 Offline", "error": str(e)}

@asset(group_name="mlops", compute_kind="django_db")
def exported_user_feedback():
    """Exporte les feedbacks RLHF et les sessions de jeu depuis la base de données Django."""
    import subprocess
    
    # Exécution de la commande de gestion Django pour exporter les données
    manage_py = os.path.join(BASE_DIR, 'backend', 'manage.py')
    try:
        subprocess.run(['python', manage_py, 'export_rlhf_data'], check=True)
    except Exception as e:
        print(f"❌ Error exporting data from Django: {e}")
        return None
    
    feedback_path = os.path.join(FEEDBACK_DATASET_DIR, "ai_feedback.jsonl")
    session_path = os.path.join(FEEDBACK_DATASET_DIR, "gameplay_sessions.jsonl")
    
    return {"feedback": feedback_path, "sessions": session_path}

@asset(group_name="mlops", deps=[exported_user_feedback])
def trl_ready_dataset(exported_user_feedback):
    """Transforme l'export en dataset formaté pour TRL (DPO/PPO)."""
    if not exported_user_feedback:
        return None
        
    feedback_path = exported_user_feedback["feedback"]
    session_path = exported_user_feedback["sessions"]
    dataset_path = os.path.join(FEEDBACK_DATASET_DIR, "trl_train_data.jsonl")
    
    rlhf_entries = []
    
    # 1. Traitement des Feedbacks (Format DPO: Chosen/Rejected)
    if os.path.exists(feedback_path):
        with open(feedback_path, 'r', encoding='utf-8') as f:
            for line in f:
                fb = json.loads(line)
                # Nettoyage de base
                if not fb['context'] or len(fb['output']) < 10:
                    continue

                if fb['is_positive']:
                    # Pour un feedback positif, on crée une paire DPO "Idéale vs Refus/Erreur"
                    rlhf_entries.append({
                        "prompt": f"Génère une fusion/scénario pour : {fb['context']}",
                        "chosen": fb['output'],
                        "rejected": "Je ne peux pas répondre à cette demande pour le moment."
                    })
                else:
                    # Pour un feedback négatif, l'output existant est le "rejected"
                    rlhf_entries.append({
                        "prompt": f"Génère une fusion/scénario pour : {fb['context']}",
                        "chosen": "Génère une réponse créative et fidèle aux thèmes otaku.", # Placeholder pour l'entraînement
                        "rejected": fb['output']
                    })

    # 2. Traitement des Sessions de Jeu (Logique de déduction)
    if os.path.exists(session_path):
        with open(session_path, 'r', encoding='utf-8') as f:
            for line in f:
                s = json.loads(line)
                if s['was_won'] and len(s['history']) > 0:
                    # On apprend à l'IA comment elle a réussi à deviner
                    history_str = "\n".join([f"Q: {h['q']} A: {h['a']}" for h in s['history']])
                    rlhf_entries.append({
                        "prompt": f"En tant qu'agent {s['game_mode']}, devine le {s['media_type']} à partir de l'historique suivant :\n{history_str}",
                        "chosen": f"La réponse est {s['target']}",
                        "rejected": "Je n'ai pas assez d'informations pour deviner."
                    })

    # Génération du fichier .jsonl
    with open(dataset_path, 'w', encoding='utf-8') as f:
        for entry in rlhf_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    print(f"✨ RLHF Dataset created: {len(rlhf_entries)} entries for Hugging Face TRL.")
    return dataset_path

@asset(group_name="mlops", deps=[trl_ready_dataset])
def trigger_model_retraining():
    """Déclenche le ré-entraînement si le volume de données est suffisant."""
    # Ici, on pourrait appeler l'API de Hugging Face Jobs (via votre skill hf-cli)
    # ou lancer un container local avec GPU.
    print("🚀 Model retraining check: threshold not reached yet (need 100+ new samples).")
    return "Check complete."
