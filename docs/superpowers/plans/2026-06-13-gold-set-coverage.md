# Gold Set Coverage Analysis & Gap Filling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a script to analyze the thematic and entity coverage of our Gold Set compared to Neo4j and Chroma, and automatically generate LLM-synthesized QA entries to fill any gaps.

**Architecture:** Create an audit script that checks missing expected entities in Neo4j and under-represented genres in Chroma, uses the default LLM adapter to synthesize entries for these gaps, and saves them to the Gold Set with evolved schema fields.

**Tech Stack:** Python, Django, Neo4j, Chroma/PGVector, pytest, Pydantic

---

### Task 1: Create the Coverage Analyzer Script

**Files:**
- Create: `backend/scripts/analyze_gold_coverage.py`

- [ ] **Step 1: Write the basic structure of the coverage analyzer script**

Create `backend/scripts/analyze_gold_coverage.py` containing:
```python
# -*- coding: utf-8 -*-
import os
import sys
import json
import logging
from typing import List, Dict, Set, Any

# Root setups
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "api"))
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
try:
    django.setup()
except Exception:
    # Handle test environment settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'animetix_project.test_settings'
    django.setup()

from animetix.containers import get_container
from animetix.models import VectorRecord
from core.domain.services.ragas_eval_service import EvaluationResult

logger = logging.getLogger("animetix.scripts.coverage")

def analyze_coverage(threshold: float = 0.05) -> Dict[str, Any]:
    gold_path = os.path.join(BASE_DIR, "data", "mlops", "gold_dataset.json")
    if not os.path.exists(gold_path):
        return {"error": "Gold dataset missing"}

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    # 1. Gather expected_entities from Gold Set
    gold_entities = set()
    gold_genres = {}
    for entry in gold_data:
        for ent in entry.get("expected_entities", []):
            gold_entities.add(ent.lower().strip())
        # Track genres mentioned in metadata or expected_entities
        genre = entry.get("domain", "general")
        gold_genre = entry.get("query_type", "standard")
        # For simplicity, we can extract query domain/genre mapping
        
    # 2. Query Neo4j for Media
    container = get_container()
    neo4j_manager = container.graph_persistence_port()
    
    missing_media = []
    if neo4j_manager.driver:
        try:
            with neo4j_manager.driver.session() as session:
                result = session.run("""
                    MATCH (m:Media)
                    OPTIONAL MATCH (m)-[r]-()
                    RETURN m.title AS title, m.id AS id, count(r) AS degree
                    ORDER BY degree DESC
                    LIMIT 20
                """)
                for record in result:
                    title = record["title"]
                    m_id = record["id"]
                    if title and title.lower().strip() not in gold_entities:
                        missing_media.append({"title": title, "id": m_id})
        except Exception as e:
            logger.warning(f"Neo4j query failed: {e}")

    # 3. Query Chroma metadata counts via VectorRecord Django model
    total_vectors = VectorRecord.objects.filter(collection_name="anime_thematic").count()
    under_represented_genres = []
    
    if total_vectors > 0:
        # Aggregate genres from Chroma records
        db_genres = {}
        records = VectorRecord.objects.filter(collection_name="anime_thematic")
        for r in records:
            genre = r.metadata.get("genre")
            if genre:
                db_genres[genre] = db_genres.get(genre, 0) + 1
                
        # Count genre occurrences in gold set
        gold_genre_counts = {}
        for entry in gold_data:
            # Look up if any expected entity has a genre or check query/contexts
            pass

    return {
        "missing_media": missing_media,
        "under_represented_genres": under_represented_genres
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument("--generate-missing", action="store_true")
    args = parser.parse_args()
    
    report = analyze_coverage(threshold=args.threshold)
    print(json.dumps(report, indent=2))
```

- [ ] **Step 2: Commit initial structure**

```bash
git add backend/scripts/analyze_gold_coverage.py
git commit -m "chore: scaffold analyze_gold_coverage.py"
```

---

### Task 2: Implement Coverage Logic and LLM Generation

**Files:**
- Modify: `backend/scripts/analyze_gold_coverage.py`

- [ ] **Step 1: Write complete coverage analysis and generation logic**

Update `backend/scripts/analyze_gold_coverage.py` to:
```python
# -*- coding: utf-8 -*-
import os
import sys
import json
import logging
from typing import List, Dict, Set, Any
from pydantic import BaseModel, Field

# Root setups
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "api"))
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
try:
    django.setup()
except Exception:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'animetix_project.test_settings'
    django.setup()

from animetix.containers import get_container
from animetix.models import VectorRecord
from django.db.models import Count

logger = logging.getLogger("animetix.scripts.coverage")

# Pydantic schema for LLM structured output
class GoldSetEntrySchema(BaseModel):
    query: str = Field(description="The question testing the RAG system.")
    ground_truth: str = Field(description="Detailed factual answer summarizing the fact/subgraph.")
    expected_entities: List[str] = Field(description="Named entities in the question/answer that must be traversed.")
    expected_contexts: List[str] = Field(description="Context blocks used for generation.")
    expected_chunks: List[str] = Field(description="Database chunk IDs associated with the source documents.")
    query_type: str = Field(description="Must be either 'graph' or 'thematic' or 'cross-media'.")
    difficulty: str = Field(description="Must be 'easy', 'medium', or 'hard'.")

def analyze_coverage(threshold: float = 0.05) -> Dict[str, Any]:
    gold_path = os.path.join(BASE_DIR, "data", "mlops", "gold_dataset.json")
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
        # Look for typical genres in the queries
        for g in ["action", "comedy", "romance", "cyberpunk", "mecha", "shonen", "shojo", "isekai"]:
            if g in query:
                gold_genres.add(g)

    # 2. Query Neo4j for Media
    container = get_container()
    neo4j_manager = container.graph_persistence_port()
    
    missing_media = []
    if neo4j_manager.driver:
        try:
            with neo4j_manager.driver.session() as session:
                result = session.run("""
                    MATCH (m:Media)
                    OPTIONAL MATCH (m)-[r]-()
                    RETURN m.title AS title, m.id AS id, count(r) AS degree
                    ORDER BY degree DESC
                    LIMIT 20
                """)
                for record in result:
                    title = record["title"]
                    m_id = record["id"]
                    if title and title.lower().strip() not in gold_entities:
                        missing_media.append({"title": title, "id": m_id})
        except Exception as e:
            logger.warning(f"Neo4j query failed: {e}")

    # 3. Query Chroma metadata counts via VectorRecord Django model
    records = VectorRecord.objects.filter(collection_name="anime_thematic")
    total_vectors = records.count()
    under_represented_genres = []
    
    if total_vectors > 0:
        db_genres = {}
        for r in records:
            genre = r.metadata.get("genre")
            if genre:
                db_genres[genre.lower().strip()] = db_genres.get(genre.lower().strip(), 0) + 1
                
        # Compare proportion in DB vs Gold Set
        for genre, count in db_genres.items():
            db_ratio = count / total_vectors
            if db_ratio > threshold and genre not in gold_genres:
                under_represented_genres.append(genre)

    return {
        "missing_media": missing_media,
        "under_represented_genres": under_represented_genres
    }

def generate_and_append_missing(report: Dict[str, Any]):
    gold_path = os.path.join(BASE_DIR, "data", "mlops", "gold_dataset.json")
    if not os.path.exists(gold_path):
        return
        
    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    container = get_container()
    inference_engine = container.inference_engine()
    neo4j_manager = container.graph_persistence_port()
    
    new_entries = []

    # A. Generate for missing media nodes
    for media in report.get("missing_media", [])[:3]:  # Limit to 3 to prevent token exhaustion
        title = media["title"]
        m_id = media["id"]
        
        # Query Neo4j for 1-hop facts
        facts = []
        if neo4j_manager.driver:
            try:
                with neo4j_manager.driver.session() as session:
                    res = session.run("""
                        MATCH (m:Media {id: $mid})-[r]->(target)
                        RETURN type(r) AS rel_type, target.name AS target_name, target.title AS target_title
                        LIMIT 5
                    """, mid=str(m_id))
                    for row in res:
                        rel = row["rel_type"]
                        name = row["target_name"] or row["target_title"]
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
                system_prompt="Tu es un générateur de dataset RAG précis."
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
                system_prompt="Tu es un générateur de dataset RAG précis."
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
        logger.info(f"Successfully appended {len(new_entries)} new entries to the Gold Set.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument("--generate-missing", action="store_true")
    args = parser.parse_args()
    
    report = analyze_coverage(threshold=args.threshold)
    print(json.dumps(report, indent=2))
    
    if args.generate-missing:
        generate_and_append_missing(report)
```

- [ ] **Step 2: Commit implementation**

```bash
git add backend/scripts/analyze_gold_coverage.py
git commit -m "feat: complete analyze_gold_coverage.py logic"
```

---

### Task 3: Create Unit Tests

**Files:**
- Create: `tests/mlops/test_gold_coverage_analyzer.py`

- [ ] **Step 1: Write unit tests verifying coverage calculation & LLM generation**

Create `tests/mlops/test_gold_coverage_analyzer.py` containing:
```python
import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

# Ensure correct backend imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

@pytest.fixture
def mock_neo4j():
    with patch("pipeline.neo4j_client.neo4j_manager") as mock:
        mock_session = MagicMock()
        mock_record1 = {"title": "Death Note", "id": "1535"}
        mock_record2 = {"title": "Bleach", "id": "154"}
        mock_session.run.return_value = [mock_record1, mock_record2]
        
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock.driver = mock_driver
        yield mock

@pytest.fixture
def mock_inference_engine():
    with patch("animetix.containers.get_container") as mock_container:
        mock_engine = MagicMock()
        mock_result = MagicMock()
        mock_result.dict.return_value = {
            "query": "Quel est l'auteur de Bleach ?",
            "ground_truth": "Tite Kubo",
            "expected_entities": ["Bleach", "Tite Kubo"],
            "expected_contexts": ["Bleach est un manga de Tite Kubo."],
            "expected_chunks": ["154"],
            "query_type": "graph",
            "difficulty": "easy"
        }
        mock_engine.generate_structured.return_value = mock_result
        
        mock_container_instance = MagicMock()
        mock_container_instance.inference_engine.return_value = mock_engine
        mock_container.return_value = mock_container_instance
        yield mock_engine

@pytest.mark.django_db
def test_analyze_coverage_identifies_gaps(mock_neo4j, mock_inference_engine, tmp_path):
    # Setup mock gold dataset
    mock_gold_data = [
        {
            "query": "Qui est Light Gami dans Death Note ?",
            "expected_entities": ["Death Note", "Light Yagami"],
            "domain": "shonen",
            "query_type": "standard",
            "ground_truth": "Light Yagami est le protagoniste de Death Note."
        }
    ]
    
    mock_file = tmp_path / "gold_dataset.json"
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(mock_gold_data, f)
        
    with patch("scripts.analyze_gold_coverage.BASE_DIR", str(tmp_path)):
        # Import inside patch
        from scripts.analyze_gold_coverage import analyze_coverage, generate_and_append_missing
        
        # Verify coverage identification
        report = analyze_coverage(threshold=0.01)
        assert len(report["missing_media"]) > 0
        
        # Verify title 'Bleach' is missing, but 'Death Note' is not
        missing_titles = [m["title"] for m in report["missing_media"]]
        assert "Bleach" in missing_titles
        assert "Death Note" not in missing_titles
        
        # Run generation
        # Patch the target json file path for writing
        with patch("scripts.analyze_gold_coverage.BASE_DIR", str(tmp_path)):
            generate_and_append_missing(report)
            
        # Verify it appended Bleach entry
        with open(mock_file, "r", encoding="utf-8") as f:
            updated_data = json.load(f)
            
        assert len(updated_data) > len(mock_gold_data)
        assert updated_data[-1]["query"] == "Quel est l'auteur de Bleach ?"
```

- [ ] **Step 2: Commit tests**

```bash
git add tests/mlops/test_gold_coverage_analyzer.py
git commit -m "test: add unit tests for Gold Set coverage analyzer"
```

---

### Task 4: Execution & Verification

**Files:**
- None (terminal verification)

- [ ] **Step 1: Run the tests to make sure they pass**

Run:
```bash
.venv/Scripts/python.exe -m pytest tests/mlops/test_gold_coverage_analyzer.py
```
Expected: PASS

- [ ] **Step 2: Dry run of coverage analyzer on the dev environment**

Run:
```bash
.venv/Scripts/python.exe backend/scripts/analyze_gold_coverage.py --threshold 0.1
```
Expected: Prints a valid JSON containing missing media from the database.

---

### Task 5: Finalize & Document

**Files:**
- Modify: `TODO.md`

- [ ] **Step 1: Check off TODO.md item**

Mark `[x] **Augmentation de la diversité & analyse de couverture**` in `TODO.md`.

- [ ] **Step 2: Commit TODO.md**

```bash
git add TODO.md
git commit -m "docs: complete Gold Set coverage analysis task"
```
