import os
import asyncio
import time
import requests
import wandb
from typing import List, Dict
from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.metrics import Faithfulness, AnswerRelevancy
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from dotenv import load_dotenv

load_dotenv()

# Initialize W&B
wandb.login(key=os.getenv("WANDB_API_KEY"))

# Configuration for evaluation models
eval_llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    google_api_key=os.getenv("GEMINI_API_KEY"),
    timeout=120,
    max_retries=3
)
eval_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)
ragas_embeddings = LangchainEmbeddingsWrapper(eval_embeddings)

# Limit workers for free tier
run_config = RunConfig(max_workers=1)

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

    print(f"\n🚀 Evaluating Engine: {engine_name}")
    
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
            response = requests.post(BRAIN_URL, json={
                "prompt": q,
                "system_prompt": "Tu es un expert en Anime/Manga."
            }, timeout=60)
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
        print(f"✅ Q: {q} | Latency: {latency:.2f}s")

    # Ragas Evaluation
    dataset = Dataset.from_dict(data)
    result = evaluate(
        dataset,
        metrics=[Faithfulness(), AnswerRelevancy()],
        llm=eval_llm,
        embeddings=ragas_embeddings,
        run_config=run_config
    )

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
    res = requests.get("http://127.0.0.1:7860/")
    engine = res.json().get("engine", "unknown")
    
    await evaluate_model(engine, {"model_type": engine, "task": "comparison"})
    
    print("\n💡 Tip: To compare, stop the local model or rename the folder to force 'Fallback-API' and run this script again.")

if __name__ == "__main__":
    asyncio.run(main())
