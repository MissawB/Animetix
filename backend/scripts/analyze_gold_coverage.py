# -*- coding: utf-8 -*-
import json
import logging
import os
import sys
from typing import Any, Dict, List

from pydantic import BaseModel, Field

# Root setups
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
from animetix.models import VectorRecord  # noqa: E402
from pipeline.logging_setup import setup_logging  # noqa: E402

logger = logging.getLogger("animetix.scripts.coverage")
setup_logging()


# Pydantic schema for LLM structured output
class GoldSetEntrySchema(BaseModel):
    query: str = Field(description="The question testing the RAG system.")
    ground_truth: str = Field(
        description="Detailed factual answer summarizing the fact/subgraph."
    )
    expected_entities: List[str] = Field(
        description="Named entities in the question/answer that must be traversed."
    )
    expected_contexts: List[str] = Field(
        description="Context blocks used for generation."
    )
    expected_chunks: List[str] = Field(
        description="Database chunk IDs associated with the source documents."
    )
    query_type: str = Field(
        description="Must be either 'graph' or 'thematic' or 'cross-media'."
    )
    difficulty: str = Field(description="Must be 'easy', 'medium', or 'hard'.")


def analyze_coverage(threshold: float = 0.05) -> Dict[str, Any]:
    gold_path = os.path.join(PROJECT_ROOT, "data", "mlops", "gold_dataset.json")
    if not os.path.exists(gold_path):
        return {"error": "Gold dataset missing"}

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    # 1. Gather expected_entities from Gold Set
    gold_entities = set()
    gold_genres = set()
    for entry in gold_data:
        for ent in entry.get("expected_entities", []):
            gold_entities.add(ent.lower().strip())
        # Try to infer covered genres from queries
        query = entry.get("query", "").lower()
        for g in [
            "action",
            "comedy",
            "romance",
            "cyberpunk",
            "mecha",
            "shonen",
            "shojo",
            "isekai",
        ]:
            if g in query:
                gold_genres.add(g)

    # 2. Query Neo4j for Media
    container = get_container()
    neo4j_manager = container.persistence.graph_persistence_port()

    missing_media = []
    if neo4j_manager.check_health():
        try:
            query = """
                MATCH (m:Media)
                OPTIONAL MATCH (m)-[r]-()
                RETURN m.title AS title, m.id AS id, count(r) AS degree
                ORDER BY degree DESC
                LIMIT 20
            """
            result = neo4j_manager.execute_read(query)
            for record in result:
                title = record["title"]
                m_id = record["id"]
                if title and title.lower().strip() not in gold_entities:
                    missing_media.append({"title": title, "id": m_id})
        except Exception as e:
            logger.warning(f"Neo4j query failed: {e}")

    # 3. Query pgvector metadata counts via VectorRecord Django model
    records = VectorRecord.objects.filter(collection_name="anime_thematic")
    total_vectors = records.count()
    under_represented_genres = []

    if total_vectors > 0:
        db_genres: dict[str, int] = {}
        for r in records:
            genre = r.metadata.get("genre")
            if genre:
                db_genres[genre.lower().strip()] = (
                    db_genres.get(genre.lower().strip(), 0) + 1
                )

        # Compare proportion in DB vs Gold Set
        for genre, count in db_genres.items():
            db_ratio = count / total_vectors
            if db_ratio > threshold and genre not in gold_genres:
                under_represented_genres.append(genre)

    return {
        "missing_media": missing_media,
        "under_represented_genres": under_represented_genres,
    }


def generate_and_append_missing(report: Dict[str, Any]):
    gold_path = os.path.join(PROJECT_ROOT, "data", "mlops", "gold_dataset.json")
    if not os.path.exists(gold_path):
        return

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    container = get_container()
    inference_engine = container.inference_engine()
    neo4j_manager = container.persistence.graph_persistence_port()

    new_entries = []

    # A. Generate for missing media nodes
    for media in report.get("missing_media", [])[
        :3
    ]:  # Limit to 3 to prevent token exhaustion
        title = media["title"]
        m_id = media["id"]

        # Query Neo4j for 1-hop facts
        facts = []
        if neo4j_manager.check_health():
            try:
                res = neo4j_manager.execute_read(
                    """
                    MATCH (m:Media {id: $mid})-[r]->(target)
                    RETURN type(r) AS rel_type, target.name AS target_name, target.title AS target_title
                    LIMIT 5
                """,
                    {"mid": str(m_id)},
                )
                for row in res:
                    rel = row["rel_type"]
                    name = row.get("target_name") or row.get("target_title")
                    if name:
                        facts.append(f"{title} is {rel} {name}")
            except Exception as e:
                logger.warning(f"Failed to query relations for {title}: {e}")

        if not facts:
            facts = [f"{title} is a popular anime/manga series."]

        prompt = f"""
        Nous voulons tester notre système de RAG. Génère un couple question/réponse précis à partir des faits suivants :
        Faits : {facts}
        """
        try:
            res_obj = inference_engine.generate_structured(
                prompt=prompt,
                response_model=GoldSetEntrySchema,
                system_prompt="Tu es un générateur de dataset RAG précis.",
            )
            entry = res_obj.dict()
            entry["is_architectural"] = False
            entry["multi_turn_history"] = []
            new_entries.append(entry)
            logger.info(f"Generated RAG entry for missing media '{title}'")
        except Exception as e:
            logger.error(f"Failed LLM generation for {title}: {e}")

    # B. Generate for under-represented genres
    for genre in report.get("under_represented_genres", [])[:2]:
        # Fetch 2 random records for this genre
        records = VectorRecord.objects.filter(collection_name="anime_thematic")
        matching = []
        for r in records:
            if r.metadata.get("genre", "").lower().strip() == genre:
                matching.append(r)
                if len(matching) >= 2:
                    break

        contexts = [r.document for r in matching if r.document]
        chunks = [r.item_id for r in matching]

        if not contexts:
            contexts = [f"Le genre {genre} est caractérisé par des thèmes spécifiques."]
            chunks = ["fallback-chunk"]

        prompt = f"""
        Génère un couple question/réponse sémantique basé sur le genre '{genre}' et le contexte ci-dessous :
        Contexte : {contexts}
        """
        try:
            res_obj = inference_engine.generate_structured(
                prompt=prompt,
                response_model=GoldSetEntrySchema,
                system_prompt="Tu es un générateur de dataset RAG précis.",
            )
            entry = res_obj.dict()
            entry["expected_contexts"] = contexts
            entry["expected_chunks"] = chunks
            entry["is_architectural"] = False
            entry["multi_turn_history"] = []
            new_entries.append(entry)
            logger.info(f"Generated RAG entry for under-represented genre '{genre}'")
        except Exception as e:
            logger.error(f"Failed LLM generation for genre {genre}: {e}")

    if new_entries:
        gold_data.extend(new_entries)
        with open(gold_path, "w", encoding="utf-8") as f:
            json.dump(gold_data, f, indent=2, ensure_ascii=False)
        logger.info(
            f"Successfully appended {len(new_entries)} new entries to the Gold Set."
        )


if __name__ == "__main__":
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument("--generate-missing", action="store_true")
    args = parser.parse_args()

    report = analyze_coverage(threshold=args.threshold)
    print(json.dumps(report, indent=2))

    if args.generate_missing:
        generate_and_append_missing(report)
