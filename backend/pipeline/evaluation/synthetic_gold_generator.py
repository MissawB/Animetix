# -*- coding: utf-8 -*-
import os
import sys
import json
import logging

# Force UTF-8 for console output on Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger("animetix.pipeline." + __name__)

# Root detection
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, BASE_DIR)

logger.info("Initializing Synthetic Gold Dataset Generator...")

try:
    from pipeline.mlops.french_market_db import FRENCH_VOICE_ACTORS  # noqa: E402, F401
    from pipeline.mlops.songs_and_seiyuu_db import (  # noqa: F401, E402
        SEIYUU_PROFILES,
        ANIME_SONGS_AND_SINGERS,
    )  # noqa: E402, F401
    from pipeline.mlops.magazines_and_awards_db import (  # noqa: F401, E402
        SERIALIZATION_MAGAZINES,
        POP_CULTURE_AWARDS,
    )  # noqa: E402, F401
except ImportError as e:
    logger.warning(f"Import error: {e}. Attempting manual path injection...")
    sys.path.insert(0, os.path.join(BASE_DIR, "backend", "pipeline", "mlops"))

# List of rich relational facts to synthesize
FACTS = [
    # French Voice Actors
    {
        "fact": "Brigitte Lecordier est la voix française d'enfance emblématique de Son Goku, Son Gohan et Son Goten dans la saga Dragon Ball.",
        "domain": "voice_actors_vf",
        "difficulty": "easy",
        "query_type": "standard",
        "expected_title": "Dragon Ball",
        "expected_id": "223",
    },
    {
        "fact": "Alexis Tomassian prête sa voix française cultissime à Light Yagami dans l'anime de thriller psychologique Death Note.",
        "domain": "voice_actors_vf",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Death Note",
        "expected_id": "1535",
    },
    {
        "fact": "Geneviève Doang est la voix française de Mikasa Ackerman dans l'adaptation animée de L'Attaque des Titans.",
        "domain": "voice_actors_vf",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Attack on Titan",
        "expected_id": "16498",
    },
    # Seiyuu
    {
        "fact": "Yuki Kaji prête sa voix originale japonaise (seiyuu) au protagoniste Eren Jäger dans L'Attaque des Titans et à Koichi Hirose dans JoJo's Bizarre Adventure.",
        "domain": "seiyuu",
        "difficulty": "hard",
        "query_type": "graph",
        "expected_title": "Multiple",
        "expected_id": "0",
    },
    {
        "fact": "Rie Takahashi est la doubleuse japonaise (seiyuu) d'Emilia dans Re:Zero et de Megumin dans KonoSuba.",
        "domain": "seiyuu",
        "difficulty": "hard",
        "query_type": "graph",
        "expected_title": "Multiple",
        "expected_id": "0",
    },
    # Anisongs
    {
        "fact": "L'artiste emblématique Aimer interprète le générique d'ouverture Zankyou Sancka pour l'arc du Quartier des Plaisirs de l'anime Demon Slayer.",
        "domain": "anisongs",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Demon Slayer",
        "expected_id": "38000",
    },
    {
        "fact": "Le groupe de rock japonais FLOW chante les openings mythiques GO!!! et Sign de l'anime Naruto Shippuden.",
        "domain": "anisongs",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Naruto",
        "expected_id": "20",
    },
    # Magazines & Awards
    {
        "fact": "Le prestigieux Prix culturel Osamu Tezuka a récompensé le manga chef-d'œuvre Monster de Naoki Urasawa en 1999.",
        "domain": "magazines",
        "difficulty": "hard",
        "query_type": "cross-media",
        "expected_title": "Monster",
        "expected_id": "19",
    },
    {
        "fact": "Le manga mythique Slam Dunk d'Takehiko Inoue a été prépublié au Japon dans le célèbre magazine Weekly Shōnen Jump.",
        "domain": "magazines",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Slam Dunk",
        "expected_id": "170",
    },
]

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"


def ask_ollama(prompt: str) -> str:
    try:
        # Dynamically inject backend path to import safe_http_request securely
        import os  # noqa: E402
        import sys  # noqa: E402

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        backend_path = os.path.join(base_dir, "backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        from core.utils.security import safe_http_request  # noqa: E402

        payload = {
            "model": "qwen3.5",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un assistant expert en structuration de données de pop culture japonaise. Réponds exclusivement en JSON valide.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        # Localhost/Ollama calls are internal, so allow_internal=True is required
        response = safe_http_request(
            "POST", OLLAMA_URL, json=payload, timeout=15, allow_internal=True
        )
        if response.status_code == 200:
            res_data = response.json()
            return res_data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama API Error or Timeout: {e}")
    return ""


def extract_neo4j_relational_patterns():
    """
    Extrait des motifs de graphe relationnels aléatoires depuis Neo4j.
    """
    logger.info("Connecting to Neo4j to extract relational patterns...")
    try:
        from pipeline.neo4j_client import neo4j_manager  # noqa: E402

        if not neo4j_manager.driver:
            logger.warning("Neo4j driver not available. Using fallback facts.")
            return []

        # Tente de récupérer des chemins de longueur 3 (Media -> Studio -> Media -> Person)
        query = """
        MATCH (m1:Media)-[:PRODUCED_BY]->(s:Studio)<-[:PRODUCED_BY]-(m2:Media)-[:CREATED_BY]->(p:Person)
        WHERE m1 <> m2
        RETURN m1.title as m1_title, m1.id as m1_id, s.name as studio_name, m2.title as m2_title, m2.id as m2_id, p.name as person_name
        LIMIT 5
        """
        records = neo4j_manager.execute_read(query)
        logger.info(f"Retrieved {len(records)} path records from Neo4j.")

        extracted_facts = []
        for r in records:
            fact_text = (
                f"L'œuvre '{r['m1_title']}' a été produite par le studio {r['studio_name']}, "
                f"qui a également produit '{r['m2_title']}', une œuvre créée par {r['person_name']}."
            )
            extracted_facts.append(
                {
                    "fact": fact_text,
                    "domain": "graph",
                    "difficulty": "hard",
                    "query_type": "graph",
                    "expected_title": r["m1_title"],
                    "expected_id": str(r["m1_id"]),
                    "expected_entities": [
                        r["m1_title"],
                        r["studio_name"],
                        r["m2_title"],
                        r["person_name"],
                    ],
                    "expected_chunks": [str(r["m1_id"]), str(r["m2_id"])],
                }
            )
        return extracted_facts
    except Exception as e:
        logger.warning(f"Error querying Neo4j for patterns: {e}. Using fallback facts.")
        return []


# Chargement dynamique des motifs Neo4j
neo4j_facts = extract_neo4j_relational_patterns()
if neo4j_facts:
    FACTS = neo4j_facts + FACTS

synthetic_gold_dataset = []

logger.info(f"Generating synthetic QA pairs for {len(FACTS)} relational motifs...")

for i, entry in enumerate(FACTS):
    fact = entry["fact"]
    logger.info(f"\n[{i + 1}/{len(FACTS)}] Synthesizing: '{fact}'")

    prompt = f"""
Basé sur le fait véridique suivant en français :
"{fact}"

Génère une question RAG en français naturel et sa réponse exacte associée.
Tu dois renvoyer STRICTEMENT un objet JSON avec la structure exacte suivante :
{{
  "query": "La question posée de manière fluide en français",
  "ground_truth": "La réponse précise contenant le fait historique ou la relation"
}}

Règles critiques :
- N'invente aucun fait en dehors de la phrase fournie.
- La sortie doit être exclusivement du JSON valide, sans aucune phrase d'introduction ni de conclusion.
"""

    response_json = ""
    success = False

    # Try calling Ollama qwen3.5
    response_raw = ask_ollama(prompt)
    if response_raw:
        try:
            parsed = json.loads(response_raw)
            if "query" in parsed and "ground_truth" in parsed:
                query = parsed["query"]
                ground_truth = parsed["ground_truth"]
                success = True
                logger.info(" -> Success via Ollama qwen3.5!")
        except Exception as pe:
            logger.error(f" -> Parse error: {pe}")

    # Safe fallback if LLM offline or chokes
    if not success:
        logger.info(" -> Fallback: Generating programmatic QA pair.")
        if entry["domain"] == "voice_actors_vf":
            query = f"Qui est le comédien ou la comédienne de doublage français qui prête sa voix à {entry['expected_title']} dans la VF ?"
            ground_truth = fact
        elif entry["domain"] == "seiyuu":
            query = "Quels personnages célèbres d'animes sont doublés en version originale japonaise par la même voix (seiyuu) ?"
            ground_truth = fact
        elif entry["domain"] == "anisongs":
            query = f"Qui interprète la chanson ou l'opening de l'anime {entry['expected_title']} ?"
            ground_truth = fact
        else:
            query = f"Dans quel magazine ou avec quel prix est lié le manga {entry['expected_title']} ?"
            ground_truth = fact

    # Structure into final RAGAS-ready gold record conforming to evolved schema
    record = {
        "query": query,
        "expected_id": entry["expected_id"],
        "expected_title": entry["expected_title"],
        "is_architectural": entry["difficulty"] == "hard",
        "query_type": entry["query_type"],
        "ground_truth": ground_truth,
        "domain": entry["domain"],
        "difficulty": entry["difficulty"],
        "contexts": [fact],
        "expected_entities": entry.get(
            "expected_entities",
            [entry["expected_title"]]
            if entry["expected_title"]
            and entry["expected_title"] not in ["None", "Multiple", "0"]
            else [],
        ),
        "expected_contexts": [fact],
        "expected_chunks": entry.get(
            "expected_chunks",
            [entry["expected_id"]]
            if entry["expected_id"] and entry["expected_id"] != "0"
            else [],
        ),
        "multi_turn_history": [],
    }

    synthetic_gold_dataset.append(record)


def push_to_hitl_gate(records):
    """
    Pousse les records générés vers le gate HITL (GoldDatasetEntry)
    pour validation humaine avant intégration.
    """
    logger.info(f"📤 Pushing {len(records)} records to HITL gate...")
    try:
        from animetix.containers import get_container  # noqa: E402

        container = get_container()

        # Tentative d'utilisation du Gate de validation (recommandé)
        try:
            validation_gate = container.synthetic_validation_service()
            count = 0
            for rec in records:
                validation_gate.validate_and_stage(
                    entry_type="QA",
                    context="\n".join(rec["contexts"]),
                    instruction=rec["query"],
                    response=rec["ground_truth"],
                    metadata=rec,
                )
                count += 1
            logger.info(
                f"✅ Successfully validated and staged {count} records via HITL gate."
            )
            return
        except Exception as ge:
            logger.warning(
                f"⚠️ Validation Gate not available or failed: {ge}. Falling back to direct port."
            )

        # Fallback sur le port direct si le gate est absent
        gold_port = container.persistence.gold_dataset_adapter()
        count = 0
        for rec in records:
            gold_port.save_synthetic_entry(
                entry_type="QA",
                context="\n".join(rec["contexts"]),
                instruction=rec["query"],
                response=rec["ground_truth"],
                metadata=rec,
            )
            count += 1
        logger.info(
            f"✅ Successfully staged {count} records in the HITL gate (direct port)."
        )
    except Exception as e:
        logger.error(f"❌ Failed to push to HITL gate: {e}")


# Output directory and write
output_dir = os.path.join(BASE_DIR, "data", "mlops")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "synthetic_gold_dataset.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(synthetic_gold_dataset, f, indent=2, ensure_ascii=False)

logger.info(
    f"✅ Generation complete! Saved exactly {len(synthetic_gold_dataset)} records to {output_path}"
)

if "--push-to-db" in sys.argv:
    push_to_hitl_gate(synthetic_gold_dataset)
