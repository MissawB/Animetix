import json
import os
import numpy as np
import requests
import wandb
from sentence_transformers import SentenceTransformer
from dagster import asset, Output, AssetObservation
import pandas as pd
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLD_DATASET = os.path.join(BASE_DIR, 'data', 'mlops', 'gold_dataset.json')

def calculate_animetix_score(metrics):
    """Calcule une note globale sur 10 basée sur les métriques RAGAS."""
    # Poids : Faithfulness (40%), Relevancy (30%), Context Recall (30%)
    f = metrics.get('faithfulness', 0)
    r = metrics.get('answer_relevancy', 0)
    cr = metrics.get('context_recall', 0)
    
    # Gestion des NaN
    f = 0 if np.isnan(f) else f
    r = 0 if np.isnan(r) else r
    cr = 0 if np.isnan(cr) else cr
    
    score = (f * 0.4 + r * 0.3 + cr * 0.3) * 10
    return round(score, 2)

@asset(group_name="mlops", deps=["anime_artifacts", "manga_artifacts"])
def ragas_performance_comparison():
    """Évaluation et comparaison RAGAS (OFFICIELLE) avec W&B."""
    if not os.path.exists(GOLD_DATASET):
        return Output(value={}, metadata={"error": "Gold dataset missing"})

    # Initialisation W&B
    api_key_wandb = os.getenv("WANDB_API_KEY")
    if api_key_wandb:
        wandb.login(key=api_key_wandb)
    
    run = wandb.init(
        project="animetix-rag-eval",
        name=f"official-run-{pd.Timestamp.now().strftime('%Y%m%d-%H%M')}",
        job_type="official-evaluation"
    )

    with open(GOLD_DATASET, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)

    # 100 entrées pour un score officiel statistiquement robuste
    # On reste sous le quota RPD de 500
    sample_size = min(100, len(gold_data))
    eval_set = gold_data[:sample_size]

    # Setup Models (Judge = 3.1 Flash Lite pour le quota)
    api_key_gemini = os.getenv("GEMINI_API_KEY")
    JUDGE_MODEL = "gemini-3.1-flash-lite-preview"
    eval_llm = ChatGoogleGenerativeAI(model=JUDGE_MODEL, google_api_key=api_key_gemini)
    eval_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key_gemini)
    ragas_embeddings = LangchainEmbeddingsWrapper(eval_embeddings)
    
    from pipeline.chroma_client import chroma_manager
    from pipeline.neo4j_client import neo4j_manager
    embed_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    brain_url = os.getenv("BRAIN_API_URL", "http://127.0.0.1:7860")

    comparison_results = {}
    summary_table = wandb.Table(columns=["Mode", "Faithfulness", "Relevancy", "Context Recall", "Animetix Score"])

    for mode in ["vector", "hybrid"]:
        print(f"⚙️ Generating answers for mode: {mode}...")
        data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
        
        for i, entry in enumerate(eval_set):
            q = entry['query']
            q_vec = embed_model.encode([q]).tolist()
            
            # Retrieval
            try:
                res = chroma_manager.query_collection("anime_thematic", q_vec, n_results=3)
                # Nettoyage des contexts (forcer string, enlever None)
                contexts = [str(doc) for doc in res['documents'][0] if doc is not None]
                if not contexts: contexts = ["Pas de contexte trouvé."]
                ids = [str(i) for i in res['ids'][0] if i is not None]
            except Exception as e:
                print(f"Chroma error: {e}")
                contexts, ids = ["Erreur technique recherche"], []
            
            if mode == "hybrid":
                try:
                    graph_ctx = neo4j_manager.get_enriched_context(ids)
                    if graph_ctx:
                        contexts = contexts + [f"Graph Metadata: {graph_ctx}"]
                except: pass
            
            # Generation (avec retry basique)
            answer = "Erreur"
            for _ in range(2):
                try:
                    resp = requests.post(f"{brain_url}/generate", json={
                        "prompt": f"Context: {contexts}\n\nQuestion: {q}",
                        "system_prompt": "Expert Anime/Manga précis."
                    }, timeout=40)
                    if resp.status_code == 200:
                        answer = resp.json().get("text", "Erreur")
                        break
                except: 
                    time.sleep(2)

            data["question"].append(q)
            data["answer"].append(answer)
            data["contexts"].append(contexts)
            data["ground_truth"].append(entry.get('expected_title', ''))
            
            if (i+1) % 10 == 0: print(f"  Processed {i+1}/{sample_size} samples...")

        # Evaluation RAGAS
        print(f"⚖️ Running RAGAS evaluation (Judge: {JUDGE_MODEL})...")
        dataset = Dataset.from_dict(data)
        try:
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=eval_llm,
                embeddings=ragas_embeddings
            )
            metrics = result.to_pandas().mean().to_dict()
            animetix_score = calculate_animetix_score(metrics)
            metrics['animetix_score'] = animetix_score
            comparison_results[mode] = metrics
            
            summary_table.add_data(
                mode, 
                metrics.get('faithfulness', 0), 
                metrics.get('answer_relevancy', 0), 
                metrics.get('context_recall', 0), 
                animetix_score
            )
            wandb.log({f"{mode}_{k}": v for k, v in metrics.items()})
        except Exception as e:
            print(f"❌ RAGAS Evaluation Error: {e}")
            comparison_results[mode] = {"error": str(e), "animetix_score": 0}

    wandb.log({"Official Comparison": summary_table})
    run.finish()

    return Output(
        value=comparison_results,
        metadata={
            "Official Vector Score": float(comparison_results['vector'].get('animetix_score', 0)),
            "Official Hybrid Score": float(comparison_results['hybrid'].get('animetix_score', 0)),
            "Dataset Size": sample_size,
            "W&B Report": run.url if api_key_wandb else "Local"
        }
    )

@asset(group_name="mlops", deps=["anime_artifacts"])
def legacy_retrieval_metrics():
    """Métriques simples de recherche (Hit Rate, MRR)."""
    evaluator = RAGEvaluator()
    metrics = evaluator.calculate_retrieval_metrics("anime_thematic")
    return Output(value=metrics, metadata=metrics)
