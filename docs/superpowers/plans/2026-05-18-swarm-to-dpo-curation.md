# Swarm-to-DPO Curation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an autonomous curation script that identifies rejected user responses and uses the Swarm (AgenticRAG) to generate "Perfect" alternatives for DPO training.

**Architecture:** A standalone script that bootstraps the Django environment, fetches `AIFeedback` entries where `is_positive=False`, and processes them using the `AgenticRAGService` to generate high-quality "chosen" responses.

**Tech Stack:** Python, Django (ORM), AgenticRAG (Swarm), DPOFeedbackLoop Service, JSONL.

---

### Task 1: Create the Swarm-to-DPO Curation Script

**Files:**
- Create: `scripts/curate_dpo_dataset.py`

- [ ] **Step 1: Implement the script logic**

```python
import os
import sys
import django
import json
from tqdm import tqdm

# Setup environment
# Assuming script is in scripts/curate_dpo_dataset.py
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.models import AIFeedback
from animetix.containers import get_container
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop

def curate_dpo_dataset():
    print("🚀 Starting Swarm-to-DPO Curation...")
    container = get_container()
    rag = container.agentic_rag
    loop = DPOFeedbackLoop(prompt_manager=container.prompt_manager)
    
    # 1. Fetch rejected feedbacks
    rejected = AIFeedback.objects.filter(is_positive=False)
    print(f"📊 Found {len(rejected)} negative feedback entries.")
    
    if not rejected.exists():
        print("ℹ️ No negative feedback to curate. Exiting.")
        return

    output_path = os.path.join(base_dir, "data", "mlops", "datasets", "dpo_train_swarm.jsonl")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    processed_count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for fb in tqdm(rejected, desc="Curation with Swarm"):
            # Generate perfect answer with Swarm
            try:
                # Use standard solve which uses Swarm/Thinking mode automatically
                # Defaulting media_type to "Anime" if not present in feedback or fixed as per task
                media_type = getattr(fb, 'media_type', 'Anime')
                chosen = rag.plan_and_solve(fb.input_context, media_type)
                
                entry = {
                    'context': fb.input_context,
                    'output': fb.output_text, # The rejected one
                    'is_positive': False
                }
                
                if loop.validate_feedback(entry):
                    pair = loop.create_dpo_pair(entry, chosen_override=chosen)
                    f.write(json.dumps(pair, ensure_ascii=False) + '\n')
                    processed_count += 1
            except Exception as e:
                print(f"   ⚠️ Failed to curate feedback {fb.id}: {e}")
                
    print(f"✨ Curation complete: {processed_count} DPO pairs saved to {output_path}")

if __name__ == "__main__":
    curate_dpo_dataset()
```

- [ ] **Step 2: Create a smoke test script to verify curation logic**

Create `tests/scripts/test_curate_dpo_dataset.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from scripts.curate_dpo_dataset import curate_dpo_dataset

@patch('scripts.curate_dpo_dataset.AIFeedback')
@patch('scripts.curate_dpo_dataset.get_container')
@patch('scripts.curate_dpo_dataset.DPOFeedbackLoop')
@patch('builtins.open', new_callable=MagicMock)
def test_curate_dpo_dataset_flow(mock_open, mock_loop_class, mock_get_container, mock_feedback):
    # Setup mocks
    mock_fb = MagicMock()
    mock_fb.input_context = "test query"
    mock_fb.output_text = "bad answer"
    mock_fb.is_positive = False
    mock_fb.id = 1
    
    mock_feedback.objects.filter.return_value = [mock_fb]
    mock_feedback.objects.filter.return_value.exists.return_value = True
    
    mock_container = MagicMock()
    mock_get_container.return_value = mock_container
    mock_rag = mock_container.agentic_rag
    mock_rag.plan_and_solve.return_value = "perfect answer"
    
    mock_loop = mock_loop_class.return_value
    mock_loop.validate_feedback.return_value = True
    mock_loop.create_dpo_pair.return_value = {"prompt": "...", "chosen": "perfect answer", "rejected": "bad answer"}
    
    # Run curation
    curate_dpo_dataset()
    
    # Verify calls
    mock_rag.plan_and_solve.assert_called_with("test query", "Anime")
    mock_loop.validate_feedback.assert_called()
    mock_loop.create_dpo_pair.assert_called_with(pytest.any, chosen_override="perfect answer")
    assert mock_open.called
```

- [ ] **Step 3: Run the smoke test**

Run: `pytest tests/scripts/test_curate_dpo_dataset.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/curate_dpo_dataset.py tests/scripts/test_curate_dpo_dataset.py
git commit -m "feat: implement Swarm-to-DPO curation script"
```
