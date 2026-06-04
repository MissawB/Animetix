# Pub/Sub & Dataflow Real-Time Lore Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Google Cloud Pub/Sub event publishing for telemetry events and a real-time wiki/lore ingestion streaming pipeline using Google Cloud Dataflow (Apache Beam) to populate the vector search database.

**Architecture:** Route DuelRoom and ArchetypeDrift events to a unified Pub/Sub topic via Django signals, publish lore ingestion scraping task URLs to another topic, and run a streaming Apache Beam pipeline on Dataflow to clean, chunk, embed, and index lore directly in ChromaDB/AlloyDB.

**Tech Stack:** Python, Django, Apache Beam, Google Cloud Pub/Sub, ChromaDB.

---

### Task 1: Update requirements.txt and install dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Append google-cloud-pubsub and apache-beam[gcp] to requirements.txt**

Modify `requirements.txt` to add the dependencies:
```text
google-cloud-pubsub==2.21.1
apache-beam[gcp]==2.56.0
```

- [ ] **Step 2: Run pip install to install the dependencies**

Run:
```bash
.venv\Scripts\pip install google-cloud-pubsub==2.21.1 apache-beam[gcp]==2.56.0
```
Expected: Successfully installed.

- [ ] **Step 3: Commit**

Run:
```bash
git add requirements.txt
git commit -m "chore: add google-cloud-pubsub and apache-beam dependencies"
```

---

### Task 2: Implement PubSubPublisherService

**Files:**
- Create: `backend/api/animetix/pubsub_service.py`

- [ ] **Step 1: Create pubsub_service.py**

Create `backend/api/animetix/pubsub_service.py` with local mock logging fallback:
```python
import os
import json
import uuid
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger("animetix.pubsub")

class PubSubPublisherService:
    def __init__(self):
        self.is_prod = getattr(settings, 'IS_PRODUCTION', False)
        self.project_id = getattr(settings, 'GCP_PROJECT_ID', 'animetix-project')
        self.client = None
        if self.is_prod:
            try:
                from google.cloud import pubsub_v1
                self.client = pubsub_v1.PublisherClient()
            except Exception as e:
                logger.error(f"Failed to initialize Pub/Sub Publisher Client: {e}")

    def publish_event(self, topic_name: str, payload: dict) -> bool:
        """Publishes an event payload to a Pub/Sub topic."""
        payload_with_meta = {
            "event_id": payload.get("event_id", str(uuid.uuid4())),
            "timestamp": payload.get("timestamp", datetime.utcnow().isoformat()),
            **payload
        }
        data = json.dumps(payload_with_meta).encode("utf-8")

        if self.client:
            try:
                topic_path = self.client.topic_path(self.project_id, topic_name)
                future = self.client.publish(topic_path, data)
                future.result(timeout=10) # resolve future to detect exceptions
                logger.info(f"Published event {payload_with_meta['event_id']} to topic {topic_name}")
                return True
            except Exception as e:
                logger.error(f"Pub/Sub publish failed for topic {topic_name}: {e}")
                return False
        else:
            logger.info(f"Simulating Pub/Sub Publish [{topic_name}]: {payload_with_meta}")
            return True
```

- [ ] **Step 2: Commit**

Run:
```bash
git add backend/api/animetix/pubsub_service.py
git commit -m "feat: implement PubSubPublisherService with local fallback logging"
```

---

### Task 3: Hook Django Signals for Pub/Sub event generation

**Files:**
- Modify: `backend/api/animetix/models.py`

- [ ] **Step 1: Update signal receivers in models.py to publish events**

Locate signal receivers for `DuelRoom` and `ArchetypeDriftSnapshot` at the bottom of `backend/api/animetix/models.py`, and append the Pub/Sub publishing logic:
```python
# Import at the end of models.py signals area
from animetix.pubsub_service import PubSubPublisherService

@receiver(post_save, sender=ArchetypeDriftSnapshot)
def trigger_drift_telemetry(sender, instance, created, **kwargs):
    if created:
        from animetix.tasks_client import enqueue_task
        enqueue_task("ingest_drift_telemetry", instance.id)
        
        # Publish to Pub/Sub
        pubsub = PubSubPublisherService()
        pubsub.publish_event("animetix-events-topic", {
            "event_type": "archetype_drift_created",
            "snapshot_id": instance.id,
            "user_id": instance.user.id,
            "archetype_id": instance.archetype_id,
            "intensity": float(instance.intensity),
            "shonen_affinity": float(instance.shonen_affinity),
            "seinen_affinity": float(instance.seinen_affinity),
            "logic_consistency": float(instance.logic_consistency)
        })

@receiver(post_save, sender=DuelRoom)
def trigger_duel_telemetry(sender, instance, created, **kwargs):
    if instance.is_finished:
        from animetix.tasks_client import enqueue_task
        enqueue_task("ingest_duel_telemetry", instance.id)
        
        # Publish to Pub/Sub
        pubsub = PubSubPublisherService()
        pubsub.publish_event("animetix-events-topic", {
            "event_type": "duel_completed",
            "room_id": instance.id,
            "player1_id": instance.player1.id if instance.player1 else None,
            "player2_id": instance.player2.id if instance.player2 else None,
            "winner_id": instance.winner.id if instance.winner else None,
            "secret_title": instance.secret_title,
            "media_type": instance.media_type
        })
```

- [ ] **Step 2: Commit**

Run:
```bash
git add backend/api/animetix/models.py
git commit -m "feat: hook Django signals to dispatch Pub/Sub events for decoupled telemetry"
```

---

### Task 4: Write Pub/Sub integration tests

**Files:**
- Create: `tests/backend/test_pubsub.py`

- [ ] **Step 1: Create test_pubsub.py**

Create `tests/backend/test_pubsub.py` containing:
```python
import logging
import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from animetix.models import DuelRoom, ArchetypeDriftSnapshot
from animetix.pubsub_service import PubSubPublisherService

def test_pubsub_service_local_mode_logs(caplog):
    service = PubSubPublisherService()
    service.is_prod = False
    
    with caplog.at_level(logging.INFO):
        res = service.publish_event(
            topic_name="animetix-events-topic",
            payload={"event_type": "test_event", "data": "hello"}
        )
    
    assert res is True
    assert "Simulating Pub/Sub Publish [animetix-events-topic]" in caplog.text

@pytest.mark.django_db
def test_signals_trigger_pubsub_publish():
    user = User.objects.create_user(username="pubsub_tester", password="pwd")
    
    with patch("animetix.pubsub_service.PubSubPublisherService.publish_event") as mock_publish:
        # Create drift snapshot
        ArchetypeDriftSnapshot.objects.create(
            user=user,
            archetype_id="Shonen",
            intensity=0.8,
            shonen_affinity=0.9,
            seinen_affinity=0.2,
            logic_consistency=0.75
        )
        assert mock_publish.call_count == 1
        args, kwargs = mock_publish.call_args
        assert args[0] == "animetix-events-topic"
        assert args[1]["event_type"] == "archetype_drift_created"
        
    with patch("animetix.pubsub_service.PubSubPublisherService.publish_event") as mock_publish:
        # Create finished DuelRoom
        DuelRoom.objects.create(
            room_code="WXYZ",
            player1=user,
            media_type="Anime",
            secret_title="Naruto",
            is_finished=True
        )
        assert mock_publish.call_count == 1
        args, kwargs = mock_publish.call_args
        assert args[0] == "animetix-events-topic"
        assert args[1]["event_type"] == "duel_completed"
```

- [ ] **Step 2: Run test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_pubsub.py -v
```
Expected: 2 passed.

- [ ] **Step 3: Commit**

Run:
```bash
git add tests/backend/test_pubsub.py
git commit -m "test: add unit tests for Pub/Sub publishing and signal triggers"
```

---

### Task 5: Implement Apache Beam lore ingestion pipeline

**Files:**
- Create: `backend/pipeline/mlops/lore_ingestion_beam.py`

- [ ] **Step 1: Create lore_ingestion_beam.py**

Create `backend/pipeline/mlops/lore_ingestion_beam.py`:
```python
import os
import re
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from typing import Dict, List

logger = logging.getLogger("animetix.pipeline.beam")

class ScrapeAndCleanDoFn(beam.DoFn):
    def process(self, element: Dict) -> List[Dict]:
        url = element.get("url")
        franchise = element.get("franchise")
        if not url:
            return []
            
        logger.info(f"Beam: Scraping URL {url} for franchise {franchise}")
        try:
            from core.utils.security import safe_http_request
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                BeautifulSoup = None
                
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = safe_http_request("GET", url, headers=headers, timeout=10)
            html = response.content
            
            if BeautifulSoup:
                soup = BeautifulSoup(html, 'html.parser')
                for tag in soup(["script", "style", "noscript", "iframe", "aside"]):
                    tag.decompose()
                content_div = soup.find(id="mw-content-text") or soup.find(class_="mw-parser-output") or soup
                text = content_div.get_text(separator=" ")
            else:
                html_str = html.decode('utf-8', errors='ignore')
                html_str = re.sub(r'<(script|style|noscript|iframe|aside)[^>]*>.*?</\1>', '', html_str, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', html_str)
                
            clean_text = re.sub(r'\s+', ' ', text).strip()[:8000]
            
            yield {
                "url": url,
                "franchise": franchise,
                "text": clean_text
            }
        except Exception as e:
            logger.error(f"Beam error scraping {url}: {e}")
            return []

class ChunkTextDoFn(beam.DoFn):
    def process(self, element: Dict) -> List[Dict]:
        text = element["text"]
        url = element["url"]
        franchise = element["franchise"]
        
        sentence_end = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_end.split(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if current_length + len(sentence) > 400 and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        yield {
            "url": url,
            "franchise": franchise,
            "chunks": chunks
        }

class GenerateEmbeddingsDoFn(beam.DoFn):
    def setup(self):
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
        try:
            django.setup()
            from animetix.containers import get_container
            self.container = get_container()
        except Exception as e:
            logger.warning(f"Django setup warning in Beam worker: {e}")
            self.container = None

    def process(self, element: Dict) -> List[Dict]:
        chunks = element["chunks"]
        url = element["url"]
        franchise = element["franchise"]
        
        results = []
        embedding_fn = None
        if self.container:
            try:
                repo = self.container.repository()
                embedding_fn = repo.embedding_fn
            except Exception as e:
                logger.error(f"Failed to get embedding function: {e}")
                
        for idx, chunk in enumerate(chunks):
            context_header = f"[Source: Fandom Lore | Franchise: {franchise.title()} | URL: {url}] "
            chunk_text = context_header + chunk
            
            # Embed chunk
            if embedding_fn:
                try:
                    vector = list(embedding_fn([chunk_text])[0])
                except Exception as e:
                    logger.error(f"Embedding generation error: {e}")
                    vector = [0.0] * 768
            else:
                # Local mock vector dimension 768
                vector = [0.1 * (idx % 10)] * 768
                
            results.append({
                "doc_id": f"beam_lore_{franchise}_{hash(url)}_{idx}",
                "chunk_text": chunk_text,
                "vector": vector,
                "metadata": {
                    "title": f"Lore {franchise.title()}",
                    "description": chunk_text,
                    "source": "Beam Real-Time Ingestion",
                    "franchise": franchise
                }
            })
            
        yield {
            "url": url,
            "franchise": franchise,
            "items": results
        }

class WriteToVectorDBDoFn(beam.DoFn):
    def setup(self):
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
        try:
            django.setup()
            from animetix.containers import get_container
            self.container = get_container()
        except Exception as e:
            logger.warning(f"Django setup warning in Beam worker: {e}")
            self.container = None

    def process(self, element: Dict) -> List[Dict]:
        items = element["items"]
        if not items:
            return []
            
        if self.container:
            try:
                repo = self.container.repository()
                collection_name = repo.coll_names.get('Anime', 'anime_thematic')
                
                ids = [x["doc_id"] for x in items]
                embeddings = [x["vector"] for x in items]
                metadatas = [x["metadata"] for x in items]
                
                repo.upsert_items(collection_name, ids, embeddings, metadatas)
                logger.info(f"Beam: Successfully upserted {len(items)} items to Vector DB")
            except Exception as e:
                logger.error(f"Beam: Error upserting items to Vector DB: {e}")
        else:
            logger.info(f"Beam Simulation: Upserting {len(items)} items to Vector DB")
            
        yield element

def run_pipeline(argv=None, test_input=None):
    pipeline_options = PipelineOptions(argv)
    
    with beam.Pipeline(options=pipeline_options) as p:
        if test_input is not None:
            # Read from static test inputs (DirectRunner Testing)
            raw_input = p | "CreateMockInput" >> beam.Create(test_input)
        else:
            # Read from streaming Pub/Sub subscription in production
            subscription_path = pipeline_options.get_all_options().get('pubsub_subscription')
            if not subscription_path:
                raise ValueError("Missing required parameter: --pubsub_subscription")
            raw_input = (
                p 
                | "ReadFromPubSub" >> beam.io.ReadFromPubSub(subscription=subscription_path)
                | "DecodeMessage" >> beam.Map(lambda bytes_data: json.loads(bytes_data.decode("utf-8")))
            )
            
        (
            raw_input
            | "ScrapeAndClean" >> beam.ParDo(ScrapeAndCleanDoFn())
            | "ChunkText" >> beam.ParDo(ChunkTextDoFn())
            | "GenerateEmbeddings" >> beam.ParDo(GenerateEmbeddingsDoFn())
            | "WriteToVectorDB" >> beam.ParDo(WriteToVectorDBDoFn())
        )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--pubsub_subscription',
        help='The Pub/Sub subscription path to read streaming tasks from.'
    )
    known_args, pipeline_args = parser.parse_known_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    run_pipeline(pipeline_args + [f"--pubsub_subscription={known_args.pubsub_subscription}"])
```

- [ ] **Step 2: Commit**

Run:
```bash
git add backend/pipeline/mlops/lore_ingestion_beam.py
git commit -m "feat: implement Dataflow Apache Beam lore ingestion streaming pipeline"
```

---

### Task 6: Write Apache Beam Pipeline unit test

**Files:**
- Create: `tests/backend/test_lore_ingestion_beam.py`

- [ ] **Step 1: Create test_lore_ingestion_beam.py**

Create `tests/backend/test_lore_ingestion_beam.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from backend.pipeline.mlops.lore_ingestion_beam import run_pipeline

class MockResponse:
    def __init__(self, content):
        self.content = content

@pytest.mark.django_db
def test_beam_pipeline_execution():
    test_input = [
        {"url": "https://onepiece.fandom.com/wiki/Luffy", "franchise": "one piece"}
    ]
    
    mock_html = b"<html><body><div id='mw-content-text'>Monkey D. Luffy is the main protagonist of One Piece. He ate the Devil Fruit.</div></body></html>"
    
    with patch("core.utils.security.safe_http_request", return_value=MockResponse(mock_html)):
        from animetix.containers import get_container
        container = get_container()
        repo = container.repository()
        
        with patch.object(repo, 'upsert_items') as mock_upsert:
            # Run in-memory using DirectRunner
            run_pipeline(
                argv=["--runner=DirectRunner"],
                test_input=test_input
            )
            
            # Assert elements were scraped, chunked, embedded and upserted
            assert mock_upsert.call_count == 1
            args, kwargs = mock_upsert.call_args
            collection_name, ids, embeddings, metadatas = args
            
            assert collection_name == "anime_thematic"
            assert len(ids) > 0
            assert "beam_lore_one piece" in ids[0]
            assert "Monkey D. Luffy" in metadatas[0]["description"]
            assert metadatas[0]["franchise"] == "one piece"
```

- [ ] **Step 2: Run test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_lore_ingestion_beam.py -v
```
Expected: 1 passed.

- [ ] **Step 3: Commit**

Run:
```bash
git add tests/backend/test_lore_ingestion_beam.py
git commit -m "test: add integration unit test for Apache Beam pipeline with DirectRunner"
```
