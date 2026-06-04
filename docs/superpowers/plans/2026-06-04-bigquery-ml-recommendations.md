# BigQuery & BigQuery ML User Recommendations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a serverless user telemetry ingestion pipeline (via Cloud Tasks) to Google Cloud BigQuery, and build a collaborative filtering recommendation engine using BigQuery ML (Matrix Factorization) to sync personalized media recommendations back to AlloyDB daily.

**Architecture:** Use Cloud Tasks to stream events asynchronously to a unified `telemetry.user_interactions` BigQuery table. A daily management command executes the matrix factorization model training on BigQuery, fetches predicted ratings, and updates a local Django `UserRecommendation` cache table in AlloyDB.

**Tech Stack:** Python, Django, Google Cloud BigQuery, Google Cloud Tasks, Pytest.

---

### Task 1: Update requirements.txt and install google-cloud-bigquery

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Append google-cloud-bigquery to requirements.txt**

Modify `requirements.txt` to add `google-cloud-bigquery==3.20.1` at the end of the file.
```text
google-cloud-bigquery==3.20.1
```

- [ ] **Step 2: Run pip install to install google-cloud-bigquery**

Run:
```bash
.venv\Scripts\pip install google-cloud-bigquery==3.20.1
```
Expected: Successfully installed.

- [ ] **Step 3: Commit**

Run:
```bash
git add requirements.txt
git commit -m "chore: add google-cloud-bigquery dependency"
```

---

### Task 2: Create UserRecommendation model in models.py

**Files:**
- Modify: `backend/api/animetix/models.py`
- Create: (Auto-generated Django migration)
- Test: `tests/backend/test_models.py`

- [ ] **Step 1: Add UserRecommendation model to models.py**

Append the model class at the end of `backend/api/animetix/models.py` (before `import json` if there is one, or just at the end of the file):
```python
class UserRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE)
    score = models.FloatField()
    rank = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rank']
        unique_together = ('user', 'media_item')

    def __str__(self):
        return f"Rec for {self.user.username}: {self.media_item.title} (Rank {self.rank})"
```

- [ ] **Step 2: Run django makemigrations and migrate**

Run:
```bash
.venv\Scripts\python backend/api/manage.py makemigrations animetix
.venv\Scripts\python backend/api/manage.py migrate
```
Expected: Migration files created and database updated successfully.

- [ ] **Step 3: Write unit tests for UserRecommendation model**

Open `tests/backend/test_models.py` and append:
```python
from animetix.models import UserRecommendation, MediaItem
from django.contrib.auth.models import User
import pytest

@pytest.mark.django_db
def test_user_recommendation_creation():
    user = User.objects.create_user(username="rec_tester", password="pwd")
    media = MediaItem.objects.create(external_id="123", media_type="Anime", title="Death Note")
    
    rec = UserRecommendation.objects.create(
        user=user,
        media_item=media,
        score=4.85,
        rank=1
    )
    
    assert rec.id is not None
    assert rec.score == 4.85
    assert rec.rank == 1
    assert str(rec) == "Rec for rec_tester: Death Note (Rank 1)"
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_models.py -k test_user_recommendation_creation -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

Run:
```bash
git add backend/api/animetix/models.py tests/backend/test_models.py backend/api/animetix/migrations/
git commit -m "feat: implement UserRecommendation model and migrations"
```

---

### Task 3: Implement BigQueryTelemetryService

**Files:**
- Create: `backend/api/animetix/bigquery_service.py`
- Create: `tests/backend/test_bigquery.py`

- [ ] **Step 1: Create bigquery_service.py with fallback logging**

Create `backend/api/animetix/bigquery_service.py`:
```python
import os
import uuid
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger("animetix.telemetry.bigquery")

class BigQueryTelemetryService:
    def __init__(self):
        self.is_prod = getattr(settings, 'IS_PRODUCTION', False)
        self.dataset_id = getattr(settings, 'GCP_BIGQUERY_DATASET', 'telemetry')
        self.client = None
        
        if self.is_prod:
            try:
                from google.cloud import bigquery
                self.client = bigquery.Client()
            except Exception as e:
                logger.error(f"Failed to initialize BigQuery Client: {e}")

    def stream_interaction(self, user_id: int, media_item_id: int, interaction_type: str, weight: float):
        """Streams a user-item interaction row to BigQuery telemetry.user_interactions."""
        row = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "media_item_id": media_item_id,
            "interaction_type": interaction_type,
            "weight": float(weight),
            "created_at": datetime.utcnow().isoformat()
        }

        if self.client:
            try:
                table_id = f"{self.client.project}.{self.dataset_id}.user_interactions"
                errors = self.client.insert_rows_json(table_id, [row])
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                    return False
                return True
            except Exception as e:
                logger.error(f"BigQuery streaming insert failed: {e}")
                return False
        else:
            logger.info(f"Simulating BigQuery Stream [user_interactions]: {row}")
            return True

    def stream_drift(self, user_id: int, archetype_id: str, intensity: float, shonen: float, seinen: float, logic: float):
        """Streams an archetype drift snapshot row to BigQuery telemetry.archetype_drift."""
        row = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "archetype_id": archetype_id,
            "intensity": float(intensity),
            "shonen_affinity": float(shonen),
            "seinen_affinity": float(seinen),
            "logic_consistency": float(logic),
            "created_at": datetime.utcnow().isoformat()
        }

        if self.client:
            try:
                table_id = f"{self.client.project}.{self.dataset_id}.archetype_drift"
                errors = self.client.insert_rows_json(table_id, [row])
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                    return False
                return True
            except Exception as e:
                logger.error(f"BigQuery streaming insert failed: {e}")
                return False
        else:
            logger.info(f"Simulating BigQuery Stream [archetype_drift]: {row}")
            return True
```

- [ ] **Step 2: Create unit test test_bigquery.py to verify fallback log mode**

Create `tests/backend/test_bigquery.py`:
```python
import logging
import pytest
from animetix.bigquery_service import BigQueryTelemetryService

def test_telemetry_service_local_mode_logs(caplog):
    # Enforce non-production
    service = BigQueryTelemetryService()
    service.is_prod = False
    service.client = None
    
    with caplog.at_level(logging.INFO):
        res = service.stream_interaction(
            user_id=42,
            media_item_id=101,
            interaction_type="duel_win",
            weight=2.0
        )
    
    assert res is True
    assert "Simulating BigQuery Stream [user_interactions]" in caplog.text
    assert "media_item_id': 101" in caplog.text
```

- [ ] **Step 3: Run the test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_bigquery.py -k test_telemetry_service_local_mode_logs -v
```
Expected: 1 passed.

- [ ] **Step 4: Commit**

Run:
```bash
git add backend/api/animetix/bigquery_service.py tests/backend/test_bigquery.py
git commit -m "feat: implement BigQueryTelemetryService with local logging simulation"
```

---

### Task 4: Register Telemetry Tasks and signals

**Files:**
- Modify: `backend/api/animetix/tasks_registry.py`
- Modify: `backend/api/animetix/tasks_views.py`
- Modify: `backend/api/animetix/models.py`
- Test: `tests/backend/test_bigquery.py`

- [ ] **Step 1: Register Cloud Tasks handlers**

Modify `backend/api/animetix/tasks_registry.py` to register the two tasks.
First, check imports and add `ingest_duel_telemetry` and `ingest_drift_telemetry` definitions:
```python
# Insert imports at the top:
from animetix.bigquery_service import BigQueryTelemetryService
from animetix.models import DuelRoom, ArchetypeDriftSnapshot, MediaItem

# Register tasks:
@register_task("ingest_duel_telemetry")
def ingest_duel_telemetry(room_id):
    try:
        room = DuelRoom.objects.get(id=room_id)
        if not room.is_finished:
            return {"status": "skipped", "reason": "room not finished"}
        
        # Look up MediaItem matching secret title
        media_item = MediaItem.objects.filter(title=room.secret_title, media_type=room.media_type).first()
        media_item_id = media_item.id if media_item else 0
        
        service = BigQueryTelemetryService()
        
        # Ingest for both players if they exist
        if room.player1:
            weight = 2.0 if room.winner == room.player1 else 1.0
            service.stream_interaction(room.player1.id, media_item_id, "duel_play", weight)
            
        if room.player2:
            weight = 2.0 if room.winner == room.player2 else 1.0
            service.stream_interaction(room.player2.id, media_item_id, "duel_play", weight)
            
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@register_task("ingest_drift_telemetry")
def ingest_drift_telemetry(snapshot_id):
    try:
        snapshot = ArchetypeDriftSnapshot.objects.get(id=snapshot_id)
        service = BigQueryTelemetryService()
        service.stream_drift(
            user_id=snapshot.user.id,
            archetype_id=snapshot.archetype_id,
            intensity=snapshot.intensity,
            shonen=snapshot.shonen_affinity,
            seinen=snapshot.seinen_affinity,
            logic=snapshot.logic_consistency
        )
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

- [ ] **Step 2: Connect Signals in models.py**

Modify the bottom of `backend/api/animetix/models.py`. Add:
```python
@receiver(post_save, sender=ArchetypeDriftSnapshot)
def trigger_drift_telemetry(sender, instance, created, **kwargs):
    if created:
        from animetix.tasks_client import enqueue_task
        enqueue_task("ingest_drift_telemetry", instance.id)

@receiver(post_save, sender=DuelRoom)
def trigger_duel_telemetry(sender, instance, created, **kwargs):
    # Only ingest if marked finished
    if instance.is_finished:
        # Prevent double ingestion via cache lock if necessary, or just rely on idempotency
        from animetix.tasks_client import enqueue_task
        enqueue_task("ingest_duel_telemetry", instance.id)
```

- [ ] **Step 3: Add unit tests to test_bigquery.py to verify signal execution**

Modify `tests/backend/test_bigquery.py` and append:
```python
from unittest.mock import patch
from django.contrib.auth.models import User
from animetix.models import DuelRoom, ArchetypeDriftSnapshot, MediaItem

@pytest.mark.django_db
def test_signals_trigger_tasks():
    user = User.objects.create_user(username="sig_tester", password="pwd")
    
    with patch("animetix.tasks_client.enqueue_task") as mock_enqueue:
        # Create drift snapshot
        ArchetypeDriftSnapshot.objects.create(
            user=user,
            archetype_id="Shonen",
            intensity=0.8,
            shonen_affinity=0.9,
            seinen_affinity=0.2,
            logic_consistency=0.75
        )
        
        mock_enqueue.assert_any_call("ingest_drift_telemetry", pytest.any(int))
        
    with patch("animetix.tasks_client.enqueue_task") as mock_enqueue:
        # Create unfinished DuelRoom (should not trigger telemetry task)
        room = DuelRoom.objects.create(
            room_code="ABCD",
            player1=user,
            media_type="Anime",
            secret_title="Naruto"
        )
        assert mock_enqueue.call_count == 0
        
        # Mark finished
        room.is_finished = True
        room.save()
        mock_enqueue.assert_called_once_with("ingest_duel_telemetry", room.id)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_bigquery.py -k test_signals_trigger_tasks -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

Run:
```bash
git add backend/api/animetix/tasks_registry.py backend/api/animetix/models.py tests/backend/test_bigquery.py
git commit -m "feat: add Django signals to trigger Cloud Tasks for BQ ingestion"
```

---

### Task 5: Implement sync_bigquery_recommendations management command

**Files:**
- Create: `backend/api/animetix/management/commands/sync_bigquery_recommendations.py`
- Test: `tests/backend/test_bigquery.py`

- [ ] **Step 1: Create management command structure and BigQuery ML SQL execution**

Create directories `backend/api/animetix/management/` and `backend/api/animetix/management/commands/` if they do not exist.
Create `backend/api/animetix/management/commands/sync_bigquery_recommendations.py`:
```python
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from animetix.models import UserRecommendation, MediaItem

class Command(BaseCommand):
    help = "Trains the BigQuery ML matrix factorization recommender model and syncs top 10 recommendations to AlloyDB."

    def handle(self, *args, **options):
        is_prod = getattr(settings, 'IS_PRODUCTION', False)
        dataset_id = getattr(settings, 'GCP_BIGQUERY_DATASET', 'telemetry')
        
        self.stdout.write("Initializing BigQuery sync process...")
        
        recs = []
        if is_prod:
            from google.cloud import bigquery
            client = bigquery.Client()
            
            # 1. Execute BigQuery ML Model Training
            train_query = f"""
            CREATE OR REPLACE MODEL `{client.project}.{dataset_id}.recommender_model`
            OPTIONS(
              model_type='matrix_factorization',
              user_col='user_id',
              item_col='media_item_id',
              rating_col='rating_weight'
            ) AS
            SELECT
              user_id,
              media_item_id,
              SUM(weight) as rating_weight
            FROM
              `{client.project}.{dataset_id}.user_interactions`
            GROUP BY
              user_id,
              media_item_id
            """
            self.stdout.write("Training BigQuery ML Model...")
            client.query(train_query).result()
            
            # 2. Get recommendations
            rec_query = f"""
            SELECT
              user_id,
              media_item_id,
              predicted_rating_weight as score,
              ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY predicted_rating_weight DESC) as rank
            FROM
              ML.RECOMMEND(MODEL `{client.project}.{dataset_id}.recommender_model`)
            WHERE
              predicted_rating_weight IS NOT NULL
            QUALIFY
              rank <= 10
            """
            self.stdout.write("Fetching top 10 recommendations...")
            query_job = client.query(rec_query)
            results = query_job.result()
            
            for row in results:
                recs.append({
                    "user_id": row["user_id"],
                    "media_item_id": row["media_item_id"],
                    "score": row["score"],
                    "rank": row["rank"]
                })
        else:
            self.stdout.write("Local dev mode: generating mock recommendations.")
            # Generate mock recommendations for testing/dev
            users = User.objects.all()
            items = MediaItem.objects.all()[:10]
            for user in users:
                for idx, item in enumerate(items):
                    recs.append({
                        "user_id": user.id,
                        "media_item_id": item.id,
                        "score": 4.5 - (idx * 0.2),
                        "rank": idx + 1
                    })
                    
        # 3. Transaction-safe database synchronization
        self.stdout.write(f"Syncing {len(recs)} recommendations to AlloyDB/PostgreSQL...")
        
        with transaction.atomic():
            # Clear old recommendations
            UserRecommendation.objects.all().delete()
            
            # Bulk Insert new ones
            new_objs = []
            for item in recs:
                try:
                    # Verify user and media item exist to avoid foreign key issues
                    user = User.objects.get(id=item["user_id"])
                    media_item = MediaItem.objects.get(id=item["media_item_id"])
                    new_objs.append(
                        UserRecommendation(
                            user=user,
                            media_item=media_item,
                            score=item["score"],
                            rank=item["rank"]
                        )
                    )
                except (User.DoesNotExist, MediaItem.DoesNotExist):
                    continue
            
            UserRecommendation.objects.bulk_create(new_objs)
            
        self.stdout.write(self.style.SUCCESS("Successfully synced recommendations!"))
```

- [ ] **Step 2: Add test to verify the management command execution**

Modify `tests/backend/test_bigquery.py` and append:
```python
from django.core.management import call_command
from animetix.models import UserRecommendation, MediaItem
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_sync_recommendations_command():
    user = User.objects.create_user(username="command_tester", password="pwd")
    media = MediaItem.objects.create(external_id="456", media_type="Anime", title="Naruto")
    
    # Assert table starts empty
    assert UserRecommendation.objects.count() == 0
    
    # Call the Django management command
    call_command("sync_bigquery_recommendations")
    
    # Assert recommendations are generated and synced (fallback mock recommendations)
    assert UserRecommendation.objects.filter(user=user).exists()
    rec = UserRecommendation.objects.get(user=user, media_item=media)
    assert rec.rank == 1
    assert rec.score == 4.5
```

- [ ] **Step 3: Run the test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_bigquery.py -k test_sync_recommendations_command -v
```
Expected: 1 passed.

- [ ] **Step 4: Commit**

Run:
```bash
git add backend/api/animetix/management/commands/sync_bigquery_recommendations.py tests/backend/test_bigquery.py
git commit -m "feat: implement sync_bigquery_recommendations command with mock fallback for dev"
```
