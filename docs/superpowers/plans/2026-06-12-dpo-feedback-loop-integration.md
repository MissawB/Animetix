# DPO Feedback Loop Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the DPO dataset compiler to the Django SQLite database via `dpo_feedback_loop.py` to query and compile real user feedback (thumbs up/down) into preference pairs, merging them directly into the final `dpo_train_validated.jsonl` dataset.

**Architecture:** Update `dpo_feedback_loop.py` to initialize the Django environment safely (preventing name shadowing of the `pipeline` package) and fetch entries from the `AIFeedback` model. Update `dpo_dataset_compiler.py` to fetch, validate, and convert database feedback entries into DPO pairs, and top up the dataset with SFT heuristic pairs if needed.

**Tech Stack:** Python 3.12, Django ORM, unittest, mock

---

### Task 1: Update dpo_feedback_loop.py to query Django database

**Files:**
- Modify: `backend/pipeline/mlops/dpo_feedback_loop.py`

- [ ] **Step 1: Setup safe Django initialization imports at the top of dpo_feedback_loop.py**

Replace lines 1-15 with the safe Python path insert and Django setup:
```python
import os
import sys
import json
import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Set up paths relative to workspace root with insert(0) to bypass name conflicts
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
api_path = os.path.join(backend_path, 'api')
if api_path not in sys.path:
    sys.path.insert(0, api_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

# Try initializing Django
django_available = False
try:
    import django
    django.setup()
    django_available = True
    from animetix.models import AIFeedback
except Exception as e:
    # Fallback to silent warning for standalone/offline execution
    pass

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger("animetix.mlops")
```

- [ ] **Step 2: Add fetch_db_feedbacks method to DPOFeedbackLoop**

Add the method `fetch_db_feedbacks` to retrieve feedback from the database:
```python
    def fetch_db_feedbacks(self) -> List[Dict[str, Any]]:
        """
        Queries AIFeedback models from Django database.
        Returns a list of dicts formatted like the JSONL feedback entries.
        """
        if not django_available:
            logger.warning("Django is not configured or available. Returning empty feedback list.")
            return []
        
        try:
            feedbacks = []
            # Query all feedback entries
            for fb in AIFeedback.objects.all():
                feedbacks.append({
                    "context": fb.input_context,
                    "output": fb.output_text,
                    "is_positive": fb.is_positive,
                    "feedback_type": fb.feedback_type
                })
            logger.info(f"Retrieved {len(feedbacks)} feedback entries from Django database.")
            return feedbacks
        except Exception as e:
            logger.warning(f"Failed to query Django AIFeedback table: {e}. Returning empty list.")
            return []
```

- [ ] **Step 3: Modify create_dpo_pair to use dynamic callbacks and skip failed oracle runs**

Update `create_dpo_pair` to:
```python
    def create_dpo_pair(self, entry: Dict, corrupt_fn = None) -> Dict:
        """
        Creates a DPO pair (Chosen/Rejected) based on user satisfaction.
        """
        prompt = f"Génère une réponse expert pour : {entry['context']}"
        
        if entry.get('is_positive'):
            # For positive feedback, the output IS the chosen sample
            # We generate a corrupted version as the rejected sample using the callback
            rejected = None
            if corrupt_fn:
                rejected = corrupt_fn(entry['output'])
            if not rejected or rejected == entry['output']:
                rejected = "Désolé, je ne peux pas traiter cette demande pour le moment."
            return {
                "prompt": prompt,
                "chosen": entry['output'],
                "rejected": rejected
            }
        else:
            # For negative feedback, the output IS the rejected sample
            # We generate the chosen sample via Gemini (Oracle)
            chosen_response = self.generate_oracle_response(entry['context'])
            # If oracle generation fails or returns default refusal, we return None (will be skipped)
            default_refusal = "Désolé, je ne dispose pas d'informations supplémentaires sur ce sujet."
            if chosen_response == default_refusal or not chosen_response:
                return None
            return {
                "prompt": prompt,
                "chosen": chosen_response,
                "rejected": entry['output']
            }
```

- [ ] **Step 4: Update process_and_export method to handle skipped pairs**

Update `process_and_export` to check for `None` pairs:
```python
    def process_and_export(self, raw_data_path: str, output_path: str, corrupt_fn = None) -> int:
        """
        Processes raw feedback and exports a validated DPO dataset.
        """
        if not os.path.exists(raw_data_path):
            logger.warning(f"Raw data path {raw_data_path} does not exist.")
            return 0
            
        processed_count = 0
        with open(output_path, 'w', encoding='utf-8') as out_f:
            with open(raw_data_path, 'r', encoding='utf-8') as in_f:
                for line in in_f:
                    try:
                        fb = json.loads(line)
                        if self.validate_feedback(fb):
                            pair = self.create_dpo_pair(fb, corrupt_fn)
                            if pair is not None:
                                out_f.write(json.dumps(pair, ensure_ascii=False) + '\n')
                                processed_count += 1
                    except json.JSONDecodeError:
                        continue
                        
        logger.info(f"✨ DPO Export complete: {processed_count} pairs validated and saved to {output_path}")
        return processed_count
```

- [ ] **Step 5: Commit changes**

```bash
git add backend/pipeline/mlops/dpo_feedback_loop.py
git commit -m "feat: configure safe Django path initialization and database query in DPO feedback loop"
```

---

### Task 2: Integrate Feedback Loop into dpo_dataset_compiler.py

**Files:**
- Modify: `backend/pipeline/mlops/dpo_dataset_compiler.py`

- [ ] **Step 1: Setup safe paths at the top of dpo_dataset_compiler.py**

Add python path insert at the top:
```python
import os
import sys

# Insert paths at 0 to avoid name conflicts with virtualenv packages
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
api_path = os.path.join(backend_path, "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)
```

- [ ] **Step 2: Update compile_dpo_pairs to fetch and merge Django feedback pairs**

Modify `compile_dpo_pairs` to fetch, validate, and merge feedback pairs from the database first, then fill up with SFT heuristic pairs:
```python
def compile_dpo_pairs(sft_path: str, output_path: str, limit: int = 2000, seed: int = 42) -> int:
    """
    Lit le dataset SFT et la base Django, fusionne le feedback utilisateur,
    génère les paires DPO par corruption équilibrée, et les écrit.
    """
    random.seed(seed)
    
    # 1. Fetch real user feedback from Django database
    feedback_pairs = []
    try:
        from dpo_feedback_loop import DPOFeedbackLoop
    except ImportError:
        try:
            from backend.pipeline.mlops.dpo_feedback_loop import DPOFeedbackLoop
        except ImportError:
            DPOFeedbackLoop = None

    if DPOFeedbackLoop:
        try:
            data_dir = os.path.dirname(output_path)
            loop = DPOFeedbackLoop(data_dir=data_dir)
            db_feedbacks = loop.fetch_db_feedbacks()
            
            # Helper callback for corruption of positive feedback
            def corrupt_callback(text):
                if random.random() < 0.5:
                    return corrupt_tonal_deviation(text)
                else:
                    return corrupt_evasive_refusal(text)
                    
            for fb in db_feedbacks:
                if loop.validate_feedback(fb):
                    pair = loop.create_dpo_pair(fb, corrupt_callback)
                    if pair is not None:
                        feedback_pairs.append(pair)
            logger.info(f"Compiled {len(feedback_pairs)} DPO pairs from user feedback database.")
        except Exception as e:
            logger.warning(f"Failed to compile feedback pairs from Django database: {e}")

    if not os.path.exists(sft_path):
        logger.error(f"SFT dataset not found at: {sft_path}")
        # If SFT is missing, still write feedback pairs if any
        if feedback_pairs:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as out_f:
                for pair in feedback_pairs[:limit]:
                    out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            return min(len(feedback_pairs), limit)
        return 0

    logger.info(f"Reading SFT dataset from {sft_path}...")
    eligible_entries = []
    
    # Mots clés de refus à filtrer
    refusal_keywords = [
        "je ne peux pas", "je ne dispose pas", "désolé",
        "i cannot", "i don't have", "sorry"
    ]

    with open(sft_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if "instruction" not in entry or "output" not in entry:
                    continue
                
                output_text = entry["output"]
                instruction_text = entry["instruction"]
                
                if len(output_text) < 40:
                    continue
                
                if any(kw in output_text.lower() for kw in refusal_keywords) or \
                   any(kw in instruction_text.lower() for kw in refusal_keywords):
                    continue
                
                eligible_entries.append(entry)
            except json.JSONDecodeError:
                continue

    total_eligible = len(eligible_entries)
    logger.info(f"Found {total_eligible} eligible SFT entries for DPO conversion.")
    
    compiled_pairs = []
    compiled_pairs.extend(feedback_pairs)
    feedback_prompts = {p["prompt"] for p in feedback_pairs}
    
    remaining_limit = limit - len(compiled_pairs)
    if remaining_limit > 0:
        # Eligible SFT entries to process, excluding already compiled prompt contexts
        selected_entries = [e for e in eligible_entries if f"Génère une réponse expert pour : {e['instruction']}" not in feedback_prompts and e['instruction'] not in feedback_prompts]
        random.shuffle(selected_entries)
        selected_entries = selected_entries[:remaining_limit]
        
        strategies = ["fact", "tone", "truncation", "refusal"]
        for idx, entry in enumerate(selected_entries):
            prompt = entry["instruction"]
            chosen = entry["output"]
            lang = entry.get("language", "Français")
            strategy = strategies[idx % len(strategies)]
            
            if strategy == "fact":
                rejected = corrupt_fact_substitution(chosen, lang)
            elif strategy == "tone":
                rejected = corrupt_tonal_deviation(chosen, lang)
            elif strategy == "truncation":
                rejected = corrupt_abrupt_truncation(chosen)
            else:
                rejected = corrupt_evasive_refusal(chosen, lang)
                
            if rejected == chosen:
                rejected = corrupt_evasive_refusal(chosen, lang)
                
            compiled_pairs.append({
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected
            })
    else:
        compiled_pairs = compiled_pairs[:limit]

    # Sauvegarder au format JSONL
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        for pair in compiled_pairs:
            out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            
    logger.info(f"Successfully compiled {len(compiled_pairs)} DPO pairs saved to {output_path}")
    return len(compiled_pairs)
```

- [ ] **Step 3: Commit changes**

```bash
git add backend/pipeline/mlops/dpo_dataset_compiler.py
git commit -m "feat: integrate user feedback loop into DPO dataset compiler"
```

---

### Task 3: Write tests to verify feedback loop integration

**Files:**
- Modify: `tests/mlops/test_dpo_dataset_compiler.py`

- [ ] **Step 1: Add test_compile_dpo_pairs_with_db_feedback in test_dpo_dataset_compiler.py**

Add a test checking that the compiler successfully queries and merges DB feedback using mock objects:
```python
    def test_compile_dpo_pairs_with_db_feedback(self):
        from unittest.mock import patch, MagicMock
        from backend.pipeline.mlops.dpo_dataset_compiler import compile_dpo_pairs
        
        # Mocking fetch_db_feedbacks to simulate user feedback entries
        mock_feedbacks = [
            # 1. Thumbs up feedback (should trigger positive DPO pair generation)
            {"context": "Qui est Shinji Ikari ?", "output": "Shinji Ikari est le protagoniste de Neon Genesis Evangelion, un adolescent complexe qui pilote l'EVA-01.", "is_positive": True, "feedback_type": "thumbs_up"},
            # 2. Thumbs down feedback (should trigger Gemini Oracle chosen generation)
            {"context": "Quel studio a fait Demon Slayer ?", "output": "C'est MAPPA, non ?", "is_positive": False, "feedback_type": "thumbs_down"}
        ]
        
        with patch('backend.pipeline.mlops.dpo_feedback_loop.django_available', True), \
             patch('backend.pipeline.mlops.dpo_feedback_loop.AIFeedback') as mock_ai_feedback:
            
            # Setup mock model query results
            mock_entries = []
            for fb in mock_feedbacks:
                mock_fb = MagicMock()
                mock_fb.input_context = fb["context"]
                mock_fb.output_text = fb["output"]
                mock_fb.is_positive = fb["is_positive"]
                mock_fb.feedback_type = fb["feedback_type"]
                mock_entries.append(mock_fb)
            
            mock_ai_feedback.objects.all.return_value = mock_entries
            
            # Mock generate_oracle_response to return a valid chosen response for negative feedback
            with patch('backend.pipeline.mlops.dpo_feedback_loop.DPOFeedbackLoop.generate_oracle_response') as mock_oracle:
                mock_oracle.return_value = "Demon Slayer a été produit par le studio ufotable, connu pour son animation de haute qualité."
                
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    sft_file = os.path.join(tmpdir, "sft.jsonl")
                    output_file = os.path.join(tmpdir, "dpo.jsonl")
                    
                    # Create empty SFT file so compiler only outputs feedback pairs
                    with open(sft_file, "w", encoding="utf-8") as f:
                        pass
                        
                    compiled_count = compile_dpo_pairs(sft_file, output_file, limit=5, seed=42)
                    
                    # We expect 2 pairs compiled (both mock feedbacks validated and converted)
                    self.assertEqual(compiled_count, 2)
                    
                    with open(output_file, "r", encoding="utf-8") as f:
                        lines = [json.loads(line) for line in f]
                        
                    self.assertEqual(len(lines), 2)
                    
                    # Verify positive feedback pair
                    p1 = lines[0]
                    self.assertEqual(p1["prompt"], "Génère une réponse expert pour : Qui est Shinji Ikari ?")
                    self.assertEqual(p1["chosen"], "Shinji Ikari est le protagoniste de Neon Genesis Evangelion, un adolescent complexe qui pilote l'EVA-01.")
                    self.assertNotEqual(p1["rejected"], p1["chosen"])
                    
                    # Verify negative feedback pair
                    p2 = lines[1]
                    self.assertEqual(p2["prompt"], "Génère une réponse expert pour : Quel studio a fait Demon Slayer ?")
                    self.assertEqual(p2["chosen"], "Demon Slayer a été produit par le studio ufotable, connu pour son animation de haute qualité.")
                    self.assertEqual(p2["rejected"], "C'est MAPPA, non ?")
```

- [ ] **Step 2: Run pytest to verify all tests pass**

Run: `.venv\Scripts\pytest tests/mlops`
Expected: 34 passed

- [ ] **Step 3: Commit changes**

```bash
git add tests/mlops/test_dpo_dataset_compiler.py
git commit -m "test: add unit test for DPO database feedback loop integration"
```
