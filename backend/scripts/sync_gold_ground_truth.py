# -*- coding: utf-8 -*-
import os
import sys
import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# Root setup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "api"))
sys.path.insert(0, PROJECT_ROOT)

import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
try:
    django.setup()
except Exception:
    os.environ["DJANGO_SETTINGS_MODULE"] = "animetix_project.test_settings"
    django.setup()

from animetix.containers import get_container  # noqa: E402

logger = logging.getLogger("animetix.scripts.sync_gold")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


class CurationSyncSchema(BaseModel):
    is_accurate: bool = Field(
        description="True if the current ground_truth matches the Neo4j facts. False if there are factual differences."
    )
    updated_ground_truth: str = Field(
        description="If not accurate, the updated ground truth text reflecting the correct Neo4j facts. If accurate, repeat the original ground_truth."
    )
    reasoning: str = Field(
        description="Brief explanation of what facts (if any) changed or why it is accurate."
    )


class ExpectedFactsSchema(BaseModel):
    expected_facts: List[Any] = Field(
        description="List of expected facts or lists of synonyms. Example: [['74 episodes', '74 épisodes'], 'Wit Studio']"
    )


def fetch_neo4j_facts(
    neo4j_manager, mid: str, neo4j_online: bool = True
) -> Dict[str, Any]:
    if not neo4j_manager or not neo4j_online:
        return {}

    try:
        # 1. Fetch node properties
        query_node = """
        MATCH (m) WHERE m.id = $mid OR m.external_id = $mid
        RETURN properties(m) as props, labels(m) as labels
        LIMIT 1
        """
        node_res = neo4j_manager.execute_read(query_node, {"mid": str(mid)})
        if not node_res:
            return {}

        props = node_res[0].get("props", {})
        labels = node_res[0].get("labels", [])

        # 2. Fetch direct 1-hop relationships
        query_rel = """
        MATCH (m)-[r]->(target)
        WHERE m.id = $mid OR m.external_id = $mid
        RETURN type(r) as rel_type, target.name as target_name, target.title as target_title, labels(target) as target_labels
        LIMIT 15
        """
        rel_res = neo4j_manager.execute_read(query_rel, {"mid": str(mid)})
        rels = []
        for r in rel_res:
            target_name = r.get("target_name") or r.get("target_title")
            if target_name:
                rels.append(
                    {
                        "rel_type": r["rel_type"],
                        "target_name": target_name,
                        "target_labels": r.get("target_labels", []),
                    }
                )

        return {"properties": props, "labels": labels, "relationships": rels}
    except Exception as e:
        logger.error(f"Error querying Neo4j for mid {mid}: {e}")
        return {}


def update_regression_benchmark_file(new_gold_set: List[Dict[str, Any]]):
    path = os.path.join(
        PROJECT_ROOT, "backend", "pipeline", "evaluation", "regression_benchmark.py"
    )
    if not os.path.exists(path):
        logger.warning(f"regression_benchmark.py not found at {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    formatted_list = json.dumps(new_gold_set, indent=4, ensure_ascii=False)

    start_marker = "GOLD_SET = ["
    start_idx = content.find(start_marker)
    if start_idx == -1:
        logger.error("Could not find GOLD_SET declaration in regression_benchmark.py")
        return

    open_brackets = 1
    end_idx = -1
    for i in range(start_idx + len(start_marker), len(content)):
        if content[i] == "[":
            open_brackets += 1
        elif content[i] == "]":
            open_brackets -= 1
            if open_brackets == 0:
                end_idx = i + 1
                break

    if end_idx == -1:
        logger.error(
            "Could not find matching closing bracket for GOLD_SET in regression_benchmark.py"
        )
        return

    new_content = (
        content[:start_idx] + "GOLD_SET = " + formatted_list + content[end_idx:]
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    logger.info(
        "Successfully updated regression_benchmark.py with updated expected facts."
    )


def run_synchronization(dry_run: bool = False) -> Dict[str, Any]:
    gold_path = os.path.join(PROJECT_ROOT, "data", "mlops", "gold_dataset.json")
    if not os.path.exists(gold_path):
        logger.error(f"Gold dataset missing at {gold_path}")
        return {"status": "error", "reason": "Gold dataset missing"}

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    container = get_container()
    neo4j_manager = container.persistence.graph_persistence_port()
    inference_engine = container.inference_engine()

    # Verify Neo4j health once
    neo4j_online = False
    if neo4j_manager:
        try:
            neo4j_online = neo4j_manager.check_health()
        except Exception as e:
            logger.warning(f"Neo4j health check failed: {e}")

    if not neo4j_online:
        logger.warning(
            "⚠️ Neo4j knowledge graph is offline. Skipping database synchronization."
        )

    updated_count = 0
    stats = []

    # Let's import regression benchmark to sync in memory first
    from backend.pipeline.evaluation.regression_benchmark import (
        GOLD_SET as benchmark_gold_set,
    )  # noqa: E402

    updated_benchmark_set = list(benchmark_gold_set)

    for entry in gold_data:
        mid = entry.get("expected_id")
        if not mid or mid == "0" or mid == "None":
            continue

        query = entry.get("query", "")
        ground_truth = entry.get("ground_truth", "")
        if not query or not ground_truth:
            continue

        # 1. Fetch latest Neo4j details
        facts = fetch_neo4j_facts(neo4j_manager, mid, neo4j_online)
        if not facts:
            continue

        # 2. Check and rewrite Ground Truth via LLM
        prompt = f"""
        Nous voulons synchroniser la Vérité Terrain de notre Gold Set avec les données du graphe Neo4j.
        Question : '{query}'
        Vérité Terrain actuelle : '{ground_truth}'
        Données réelles à jour : {json.dumps(facts, ensure_ascii=False)}
        Est-ce que la Vérité Terrain actuelle est toujours factuellement exacte par rapport aux données réelles ?
        """
        try:
            res_obj = inference_engine.generate_structured(
                prompt=prompt,
                response_model=CurationSyncSchema,
                system_prompt="Tu es un vérificateur de faits et de synchronisation de base de données.",
            )
            sync_res = res_obj

            if not sync_res.is_accurate:
                logger.info(f"🔄 Factual drift detected for query: '{query[:50]}...'")
                logger.info(f"   Reason: {sync_res.reasoning}")
                logger.info(f"   Old GT: {ground_truth}")
                logger.info(f"   New GT: {sync_res.updated_ground_truth}")

                if not dry_run:
                    entry["ground_truth"] = sync_res.updated_ground_truth

                updated_count += 1
                stats.append(
                    {
                        "query": query,
                        "old_gt": ground_truth,
                        "new_gt": sync_res.updated_ground_truth,
                        "reasoning": sync_res.reasoning,
                    }
                )

                # 3. Synchronize regression_benchmark.py expected_facts if mapped
                for b_entry in updated_benchmark_set:
                    if b_entry["query"].lower().strip() == query.lower().strip():
                        facts_prompt = f"""
                        Génère la liste des faits attendus (expected_facts) sous forme de synonymes pour valider cette réponse.
                        Question : '{query}'
                        Vérité Terrain : '{sync_res.updated_ground_truth}'
                        Renvoie la structure JSON attendue.
                        """
                        try:
                            facts_obj = inference_engine.generate_structured(
                                prompt=facts_prompt,
                                response_model=ExpectedFactsSchema,
                                system_prompt="Tu es un extracteur de faits de test.",
                            )
                            logger.info(
                                f"   Updated benchmark facts: {facts_obj.expected_facts}"
                            )
                            if not dry_run:
                                b_entry["expected_facts"] = facts_obj.expected_facts
                        except Exception as fe:
                            logger.error(
                                f"   Failed to extract expected facts for benchmark query: {fe}"
                            )

        except Exception as e:
            logger.error(
                f"Failed structured validation for query '{query[:50]}...': {e}"
            )

    if updated_count > 0 and not dry_run:
        # Save gold dataset
        with open(gold_path, "w", encoding="utf-8") as f:
            json.dump(gold_data, f, indent=2, ensure_ascii=False)
        logger.info(
            f"Successfully synchronized {updated_count} entries in gold_dataset.json."
        )

        # Save regression benchmark
        update_regression_benchmark_file(updated_benchmark_set)

    return {"status": "success", "updated_count": updated_count, "details": stats}


if __name__ == "__main__":
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Audit dataset without saving modifications",
    )
    args = parser.parse_args()

    res = run_synchronization(dry_run=args.dry_run)
    print(json.dumps(res, indent=2, ensure_ascii=False))
