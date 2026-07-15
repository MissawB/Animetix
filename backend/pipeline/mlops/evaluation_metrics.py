import json
import logging
import os
import sys

import pandas as pd
from sentence_transformers import SentenceTransformer

try:
    import wandb
except ImportError:  # W&B is optional; only the standalone eval script uses it
    wandb = None  # type: ignore[assignment]

# Fix path for internal imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from core.utils.security import safe_http_request  # noqa: E402

logger = logging.getLogger("animetix.pipeline." + __name__)

# Chemins
GOLD_DATASET = os.path.join(PROJECT_ROOT, "data", "mlops", "gold_dataset.json")


def calculate_animetix_score(metrics):
    """Calcule une note globale sur 10 basée sur les métriques RAGAS."""
    from core.domain.services.scoring_service import ScoringDomainService  # noqa: E402

    return ScoringDomainService.calculate_animetix_ragas_score(metrics)


def ragas_performance_comparison():
    """Évaluation et comparaison RAGAS (OFFICIELLE) avec W&B par catégorie et par tranche."""
    if not os.path.exists(GOLD_DATASET):
        return {"error": "Gold dataset missing"}

    # Initialisation W&B
    api_key_wandb = os.getenv("WANDB_API_KEY")
    if api_key_wandb:
        wandb.login(key=api_key_wandb)

    run = wandb.init(
        project="animetix-rag-eval",
        name=f"official-run-{pd.Timestamp.now().strftime('%Y%m%d-%H%M')}",
        job_type="official-evaluation",
    )

    with open(GOLD_DATASET, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    # Utiliser tout le dataset pour une évaluation complète par catégorie
    len(gold_data)
    eval_set = gold_data

    # Setup custom LLM Judge Service
    from animetix.containers import get_container  # noqa: E402
    from core.domain.services.ragas_eval_service import (  # noqa: E402
        EvaluationResult,
        RagasEvalService,
    )

    eval_service = RagasEvalService(
        judge_engine=get_container().inference.inference_engine()
    )

    from pipeline.neo4j_client import neo4j_manager  # noqa: E402
    from pipeline.vector_client import vector_manager  # noqa: E402

    embed_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    brain_url = os.getenv("BRAIN_API_URL", "http://127.0.0.1:7861")
    brain_api_key = os.getenv("BRAIN_API_KEY", "dev-insecure-key-animetix-2026")

    # Registry and service for costs
    from core.domain.services.pricing_service import PricingService  # noqa: E402

    pricing_service = PricingService()

    summary_table = wandb.Table(
        columns=[
            "Mode",
            "QueryType",
            "Faithfulness",
            "Relevancy",
            "Context Recall",
            "Animetix Score",
        ]
    )

    for mode in ["vector", "hybrid"]:
        logger.info(f"⚙️ Generating answers for mode: {mode}...")
        results_list = []

        for i, entry in enumerate(eval_set):
            q = entry["query"]
            q_vec = embed_model.encode([q]).tolist()

            # Retrieval
            try:
                res = vector_manager.query_collection(
                    "anime_thematic", q_vec, n_results=3
                )
                contexts = [str(doc) for doc in res["documents"][0] if doc is not None]
                if not contexts:
                    contexts = ["Pas de contexte trouvé."]
                ids = [str(i) for i in res["ids"][0] if i is not None]
            except Exception:
                contexts, ids = ["Erreur technique recherche"], []

            if mode == "hybrid":
                try:
                    graph_ctx = neo4j_manager.get_enriched_context(ids)
                    if graph_ctx:
                        contexts = contexts + [f"Graph Metadata: {graph_ctx}"]
                except Exception as e:
                    logger.warning(f"⚠️ Graph context extraction error for {ids}: {e}")
                    pass

            # Generation
            answer = "Erreur"
            latency = 0.0
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            cost = 0.0

            import time  # noqa: E402

            start_time = time.time()
            try:
                # Assurez-vous que l'URL se termine par /generate
                actual_url = (
                    f"{brain_url}/generate"
                    if not brain_url.endswith("/generate")
                    else brain_url
                )
                resp = safe_http_request(
                    "POST",
                    actual_url,
                    json={
                        "prompt": f"Context: {contexts}\n\nQuestion: {q}",
                        "system_prompt": "Expert Anime/Manga précis.",
                    },
                    headers={"X-API-Key": brain_api_key},
                    timeout=40,
                    allow_internal=True,
                )
                latency = time.time() - start_time
                if resp.status_code == 200:
                    resp_json = resp.json()
                    answer = resp_json.get("text", "Erreur")
                    usage = resp_json.get("usage", {})
                    if usage:
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)
                        total_tokens = usage.get("total_tokens", 0)
                        cost = pricing_service.calculate_cost(
                            "brain-api", prompt_tokens, completion_tokens
                        )
                else:
                    logger.error(
                        f"❌ Brain API Error {resp.status_code} for question: {q}"
                    )
            except Exception as e:
                latency = time.time() - start_time
                logger.warning(f"⚠️ Brain API generation error: {e}")
                pass

            results_list.append(
                {
                    "question": q,
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": entry.get("ground_truth", "")
                    or entry.get("expected_title", ""),
                    "is_architectural": entry.get("is_architectural", False),
                    "query_type": entry.get("query_type", "standard"),
                    "difficulty": entry.get("difficulty", "easy"),
                    "latency": latency,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                }
            )

        # Evaluation RAGAS
        logger.info(f"⚖️ Running RAGAS evaluation (Mode: {mode})...")
        for res in results_list:
            q = res["question"]
            a = res["answer"]
            c_str = "\n".join(res["contexts"])
            gt = res["ground_truth"]

            prompt = f"""
            Évalue l'interaction RAG ci-dessous en la comparant à la Vérité Terrain (Ground Truth) attendue :
            
            Question de l'utilisateur :
            {q}
            
            Contexte de connaissances fourni :
            {c_str}
            
            Réponse générée par le système :
            {a}
            
            Vérité Terrain attendue (Ground Truth) :
            {gt}
            """
            try:
                result = eval_service.judge_engine.generate_structured(
                    prompt=prompt,
                    response_model=EvaluationResult,
                    system_prompt="Tu es un juge sémantique d'IA impartial chargé de mesurer la qualité d'une interaction RAG.",
                )
                res["faithfulness"] = float(result.faithfulness)
                res["answer_relevancy"] = float(result.answer_relevancy)
                res["context_precision"] = float(result.context_precision)
                res["context_recall"] = float(
                    result.context_recall if result.context_recall is not None else 0.0
                )

                # Calcule une note globale sur 10 basée sur les métriques RAGAS
                metrics = {
                    "faithfulness": res["faithfulness"],
                    "answer_relevancy": res["answer_relevancy"],
                    "context_precision": res["context_precision"],
                    "context_recall": res["context_recall"],
                }
                res["animetix_score"] = calculate_animetix_score(metrics)
            except Exception as e:
                logger.error(f"❌ RAGAS Evaluation Error for query '{q}': {e}")
                res["faithfulness"] = 0.0
                res["answer_relevancy"] = 0.0
                res["context_precision"] = 0.0
                res["context_recall"] = 0.0
                res["animetix_score"] = 0.0

        # Construct DataFrame
        df_results = pd.DataFrame(results_list)

        # Overall Mode metrics
        if not df_results.empty:
            overall_metrics = {
                "faithfulness": float(df_results["faithfulness"].mean()),
                "answer_relevancy": float(df_results["answer_relevancy"].mean()),
                "context_precision": float(df_results["context_precision"].mean()),
                "context_recall": float(df_results["context_recall"].mean()),
                "avg_latency": float(df_results["latency"].mean()),
                "avg_cost": float(df_results["cost"].mean()),
                "avg_total_tokens": float(df_results["total_tokens"].mean()),
            }
            overall_metrics["animetix_score"] = calculate_animetix_score(
                overall_metrics
            )
            wandb.log({f"{mode}_overall_{k}": v for k, v in overall_metrics.items()})

        # Standard vs Architectural slice
        for arch_val, q_type_name in [(True, "architectural"), (False, "standard")]:
            slice_df = df_results[df_results["is_architectural"] == arch_val]
            if not slice_df.empty:
                metrics = {
                    "faithfulness": float(slice_df["faithfulness"].mean()),
                    "answer_relevancy": float(slice_df["answer_relevancy"].mean()),
                    "context_precision": float(slice_df["context_precision"].mean()),
                    "context_recall": float(slice_df["context_recall"].mean()),
                    "avg_latency": float(slice_df["latency"].mean()),
                    "avg_cost": float(slice_df["cost"].mean()),
                    "avg_total_tokens": float(slice_df["total_tokens"].mean()),
                }
                animetix_score = calculate_animetix_score(metrics)
                metrics["animetix_score"] = animetix_score

                summary_table.add_data(
                    mode,
                    q_type_name,
                    metrics["faithfulness"],
                    metrics["answer_relevancy"],
                    metrics["context_recall"],
                    animetix_score,
                )

                # Log metrics to W&B
                wandb.log({f"{mode}_{q_type_name}_{k}": v for k, v in metrics.items()})

        # Slice Analysis by Query Type (graph, thematic, etc.)
        for q_type in df_results["query_type"].unique():
            slice_df = df_results[df_results["query_type"] == q_type]
            if not slice_df.empty:
                metrics = {
                    "faithfulness": float(slice_df["faithfulness"].mean()),
                    "answer_relevancy": float(slice_df["answer_relevancy"].mean()),
                    "context_precision": float(slice_df["context_precision"].mean()),
                    "context_recall": float(slice_df["context_recall"].mean()),
                    "avg_latency": float(slice_df["latency"].mean()),
                    "avg_cost": float(slice_df["cost"].mean()),
                    "avg_total_tokens": float(slice_df["total_tokens"].mean()),
                }
                metrics["animetix_score"] = calculate_animetix_score(metrics)

                # Log to W&B
                wandb.log(
                    {
                        f"{mode}_slice_query_type_{q_type}_{k}": v
                        for k, v in metrics.items()
                    }
                )

        # Slice Analysis by Difficulty (easy, medium, hard)
        for diff in df_results["difficulty"].unique():
            slice_df = df_results[df_results["difficulty"] == diff]
            if not slice_df.empty:
                metrics = {
                    "faithfulness": float(slice_df["faithfulness"].mean()),
                    "answer_relevancy": float(slice_df["answer_relevancy"].mean()),
                    "context_precision": float(slice_df["context_precision"].mean()),
                    "context_recall": float(slice_df["context_recall"].mean()),
                    "avg_latency": float(slice_df["latency"].mean()),
                    "avg_cost": float(slice_df["cost"].mean()),
                    "avg_total_tokens": float(slice_df["total_tokens"].mean()),
                }
                metrics["animetix_score"] = calculate_animetix_score(metrics)

                # Log to W&B
                wandb.log(
                    {
                        f"{mode}_slice_difficulty_{diff}_{k}": v
                        for k, v in metrics.items()
                    }
                )

        # Log detailed Table to W&B
        try:
            table_cols = [
                "question",
                "answer",
                "ground_truth",
                "query_type",
                "difficulty",
                "latency",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "cost",
                "faithfulness",
                "answer_relevancy",
                "context_precision",
                "context_recall",
                "animetix_score",
            ]
            wb_table = wandb.Table(columns=table_cols)
            for _, row in df_results.iterrows():
                wb_table.add_data(*(row[col] for col in table_cols))
            wandb.log({f"{mode}_detailed_results": wb_table})
        except Exception as e:
            logger.error(f"❌ Error logging detailed table to W&B: {e}")

    wandb.log({"Official Comparison": summary_table})
    run.finish()

    return {"status": "completed"}


def legacy_retrieval_metrics():
    """Métriques simples de recherche (Hit Rate, MRR)."""
    # Importation différée pour éviter des dépendances circulaires
    from pipeline.mlops.evaluation_metrics_evaluator import RAGEvaluator  # noqa: E402

    evaluator = RAGEvaluator()
    metrics = evaluator.calculate_retrieval_metrics("anime_thematic")
    return metrics
