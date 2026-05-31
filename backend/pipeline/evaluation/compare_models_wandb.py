import os
import asyncio
import time
import httpx
import wandb
import logging
from typing import List, Dict
# --- DJANGO SETUP FOR MLOPS CONTAINERS ---
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.containers import get_container
from core.domain.services.ragas_eval_service import RagasEvalService, EvaluationResult

from dotenv import load_dotenv
load_dotenv()
from core.utils.security import safe_http_request
logger = logging.getLogger("animetix." + __name__)
if os.getenv("WANDB_API_KEY"):
    wandb.login(key=os.getenv("WANDB_API_KEY"))

BRAIN_URL = "http://127.0.0.1:7860/generate"

# Test set extracted from dataset
TEST_SET = [
    {
        "question": "Qui est Kenichirou Ryuuzaki ?",
        "ground_truth": "Kenichirou Ryuuzaki est un ami d'Akira Tendou dans Zom 100. Il était commercial avant l'apocalypse et voulait devenir comédien."
    },
    {
        "question": "Qui est Halkara ?",
        "ground_truth": "Halkara est une elfe et apprentie d'Azusa dans Slime Taoshite 300-nen. Elle est PDG d'une entreprise de champignons."
    },
    {
        "question": "Analyse le personnage de Kabru dans Dungeon Meshi.",
        "ground_truth": "Kabru est le leader de son groupe dans Dungeon Meshi. Il est socialement intelligent, analytique et motivé par la destruction de son village natal."
    },
    {
        "question": "Quelles sont les thématiques du manga 'Jibi Eopseo' ?",
        "ground_truth": "Homeless, Found Family, Coming of Age, School, Tragedy, Comedy, Drama."
    }
]

async def evaluate_model(engine_name: str, config: Dict):
    """Evaluates the brain API and logs to W&B."""
    run = wandb.init(
        project="animetix-brain-comparison",
        name=f"eval-{engine_name}-{int(time.time())}",
        config=config
    )

    logger.info(f"🚀 Evaluating Engine: {engine_name}")
    
    data = {
        "question": [],
        "answer": [],
        "contexts": [], # We simulate context for now or keep empty if model has its own RAG
        "ground_truth": []
    }

    latencies = []

    for item in TEST_SET:
        q = item["question"]
        gt = item["ground_truth"]
        
        start_time = time.time()
        try:
            response = safe_http_request("POST", BRAIN_URL, json={
                "prompt": q,
                "system_prompt": "Tu es un expert en Anime/Manga."
            }, timeout=60, allow_internal=True)
            latency = time.time() - start_time
            latencies.append(latency)
            
            if response.status_code == 200:
                answer = response.json().get("text", "")
            else:
                answer = f"Error: {response.status_code}"
        except Exception as e:
            answer = f"Exception: {e}"
            latency = time.time() - start_time
            latencies.append(latency)

        data["question"].append(q)
        data["answer"].append(answer)
        data["contexts"].append(["No specific context provided in this direct test."])
        data["ground_truth"].append(gt)
        logger.info(f"✅ Q: {q} | Latency: {latency:.2f}s")

    # Setup custom LLM Judge Service
    eval_service = RagasEvalService(judge_engine=get_container().inference_engine())
    
    faith_scores = []
    relevance_scores = []
    
    for i in range(len(data["question"])):
        q = data["question"][i]
        a = data["answer"][i]
        c = "\n".join(data["contexts"][i])
        gt = data["ground_truth"][i]
        
        prompt = f"""
        Évalue l'interaction RAG ci-dessous en la comparant à la Vérité Terrain (Ground Truth) attendue :
        
        Question de l'utilisateur :
        {q}
        
        Contexte de connaissances fourni :
        {c}
        
        Réponse générée par le système :
        {a}
        
        Vérité Terrain attendue (Ground Truth) :
        {gt}
        """
        
        try:
            res_obj = eval_service.judge_engine.generate_structured(
                prompt=prompt,
                response_model=EvaluationResult,
                system_prompt="Tu es un juge sémantique d'IA impartial chargé de mesurer la qualité d'une interaction RAG."
            )
            faith_scores.append(res_obj.faithfulness)
            relevance_scores.append(res_obj.answer_relevancy)
        except Exception as e:
            logger.error(f"Error judging row in compare_models_wandb: {e}")
            faith_scores.append(0.0)
            relevance_scores.append(0.0)
            
    result = {
        "faithfulness": sum(faith_scores) / len(faith_scores) if faith_scores else 0.0,
        "answer_relevancy": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    }

    # Logging results to W&B
    avg_latency = sum(latencies) / len(latencies)
    
    wandb.log({
        "avg_latency": avg_latency,
        "faithfulness": result["faithfulness"],
        "answer_relevancy": result["answer_relevancy"],
    })

    # Log detailed table
    table_data = []
    for i in range(len(data["question"])):
        table_data.append([
            data["question"][i],
            data["answer"][i],
            data["ground_truth"][i],
            latencies[i]
        ])
    
    wandb.log({"detailed_results": wandb.Table(
        columns=["Question", "Answer", "Ground Truth", "Latency"],
        data=table_data
    )})

    run.finish()
    return result

async def main():
    # 1. Tester le moteur actuel (Local Expert s'il est chargé)
    # On vérifie quel moteur est actif via le health check
    res = safe_http_request("GET", "http://127.0.0.1:7860/", allow_internal=True)
    engine = res.json().get("engine", "unknown")
    
    await evaluate_model(engine, {"model_type": engine, "task": "comparison"})
    
    logger.info("💡 Tip: To compare, stop the local model or rename the folder to force 'Fallback-API' and run this script again.")

if __name__ == "__main__":
    asyncio.run(main())
