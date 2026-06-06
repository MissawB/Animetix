# API Validation Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize the refactoring of views in `backend/api/animetix/views/api.py` to consistently use Django Forms and Pydantic for validation, removing direct access to `request.GET` and `request.POST`.

**Architecture:** Use Django Forms for simple GET/POST parameter validation and Pydantic for complex JSON payloads. Views are kept thin by delegating validation to these components.

**Tech Stack:** Django (Forms), Pydantic (v2), Python 3.11+.

---

### Task 1: Create Pydantic Schemas for Offline Sync

**Files:**
- Create: `backend/api/animetix/schemas.py`
- Test: `tests/api/test_schemas.py`

- [ ] **Step 1: Write the schema test**

```python
import pytest
from pydantic import ValidationError
from backend.api.animetix.schemas import OfflineSyncSchema

def test_offline_sync_schema_valid():
    data = [{"game_mode": "classic", "score": 100, "attempts": 1}]
    schema = OfflineSyncSchema.model_validate(data)
    assert len(schema.root) == 1

def test_offline_sync_schema_invalid_mode():
    data = [{"game_mode": "fictif", "score": 100}]
    with pytest.raises(ValidationError):
        OfflineSyncSchema.model_validate(data)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_schemas.py`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement the schema**

```python
from pydantic import BaseModel, Field, RootModel
from typing import List, Literal

class OfflineGameResult(BaseModel):
    game_mode: Literal[
        'classic', 'emoji', 'animinator', 'paradox', 
        'vision_quest', 'blindtest', 'covertest'
    ]
    media_type: str = "Anime"
    score: int = Field(..., ge=0, le=100)
    attempts: int = Field(1, ge=1)

class OfflineSyncSchema(RootModel):
    root: List[OfflineGameResult] = Field(..., max_length=50)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_schemas.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/schemas.py tests/api/test_schemas.py
git commit -m "api: add Pydantic schemas for offline sync"
```

---

### Task 2: Update Django Forms

**Files:**
- Modify: `backend/api/animetix/forms.py`
- Test: `tests/api/test_forms.py`

- [ ] **Step 1: Write tests for new forms**

```python
import pytest
from backend.api.animetix.forms import EmojiStreamForm, ParadoxStreamForm, AgenticRagForm, AniminatorForm

def test_emoji_stream_form_valid():
    form = EmojiStreamForm({'secret': 'item_123'})
    assert form.is_valid()
    assert form.cleaned_data['target_secret'] == 'item_123'

def test_paradox_stream_form_valid():
    form = ParadoxStreamForm({'t1': 'a', 't2': 'b', 'intruder': 'i'})
    assert form.is_valid()
    assert form.cleaned_data['item_a'] == 'a'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_forms.py`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement new forms and update AniminatorForm**

Modify `backend/api/animetix/forms.py`:
```python
class EmojiStreamForm(BaseGameForm):
    target_secret = forms.CharField(max_length=255, required=True)
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', {})
        if 'secret' in data and 'target_secret' not in data:
            data = data.copy()
            data['target_secret'] = data['secret']
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

class ParadoxStreamForm(BaseGameForm):
    item_a = forms.CharField(max_length=255, required=True)
    item_b = forms.CharField(max_length=255, required=True)
    intruder_item = forms.CharField(max_length=255, required=True)

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', {})
        # Map legacy names to descriptive names
        mapping = {'t1': 'item_a', 't2': 'item_b', 'intruder': 'intruder_item'}
        new_data = data.copy()
        for old, new in mapping.items():
            if old in data and new not in data:
                new_data[new] = data[old]
        kwargs['data'] = new_data
        super().__init__(*args, **kwargs)

class AgenticRagForm(BaseGameForm):
    query = forms.CharField(max_length=500, required=True)
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', {})
        if 'q' in data and 'query' not in data:
            data = data.copy()
            data['query'] = data['q']
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

class AniminatorForm(BaseGameForm):
    query = forms.CharField(max_length=150, required=True, label="Votre question")
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', {})
        if 'q' in data and 'query' not in data:
            data = data.copy()
            data['query'] = data['q']
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

    def clean_query(self):
        return self.clean_text('query', 150)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_forms.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/forms.py tests/api/test_forms.py
git commit -m "api: update Django forms with descriptive field mapping"
```

---

### Task 3: Refactor Streaming Views in `api.py`

**Files:**
- Modify: `backend/api/animetix/views/api.py`

- [ ] **Step 1: Refactor `emoji_decode_stream`**

Replace parameter retrieval with `EmojiStreamForm`.

- [ ] **Step 2: Refactor `paradox_stream`**

Replace parameter retrieval with `ParadoxStreamForm`.

- [ ] **Step 3: Refactor `agentic_rag_stream`**

Replace parameter retrieval with `AgenticRagForm`.

- [ ] **Step 4: Refactor `animinator_stream`**

Replace parameter retrieval with `AniminatorForm`.

- [ ] **Step 5: Verify refactoring**

Run existing smoke tests or manual verification if possible.

- [ ] **Step 6: Commit**

```bash
git add backend/api/animetix/views/api.py
git commit -m "api: refactor streaming views to use Django Forms"
```

---

### Task 4: Refactor `sync_offline_data` View

**Files:**
- Modify: `backend/api/animetix/views/api.py`

- [ ] **Step 1: Update imports**

Add `from ..schemas import OfflineSyncSchema` and `from pydantic import ValidationError`.

- [ ] **Step 2: Refactor `sync_offline_data` logic**

Use `OfflineSyncSchema.model_validate(json.loads(request.body))` and handle `ValidationError`.

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/views/api.py
git commit -m "api: refactor sync_offline_data to use Pydantic validation"
```
