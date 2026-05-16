# Qwen3-VL SOTA Video Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a SOTA (May 2026) video analysis adapter using Qwen3-VL-A3B via Hugging Face Inference API.

**Architecture:** Add a new `Qwen3VLAdapter` to the `adapters/inference` layer, implementing the `InferencePort` interface. Update the `Container` to prioritize this adapter for video-related tasks.

**Tech Stack:** Python 3.10+, `huggingface_hub` library (2026 version), Base64 encoding for local videos.

---

### Task 1: Create Qwen3VLAdapter

**Files:**
- Create: `src/adapters/inference/qwen3_vl_adapter.py`
- Test: `tests/core/test_qwen3_vl_adapter.py`

- [ ] **Step 1: Write the failing test for video analysis**
```python
import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter

@patch("adapters.inference.qwen3_vl_adapter.InferenceClient")
def test_video_analysis_calls_hf_api(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.chat_completion.return_value.choices[0].message.content = "Episode 12"
    
    adapter = Qwen3VLAdapter(token="fake_token")
    result = adapter.localize_video_actions(b"fake_video_data", ["Which episode?"])
    
    assert "Episode 12" in result[0]["answer"]
```

- [ ] **Step 2: Implement Qwen3VLAdapter**
```python
import base64
import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from huggingface_hub import InferenceClient

logger = logging.getLogger("animetix.inference.qwen3vl")

class Qwen3VLAdapter(InferencePort):
    def __init__(self, model_id: str = "Qwen/Qwen3-VL-30B-A3B-Instruct", token: str = None):
        self.client = InferenceClient(model=model_id, token=token)

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        video_b64 = base64.b64encode(video_data).decode("utf-8")
        results = []
        for query in action_queries:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "video", "video": f"data:video/mp4;base64,{video_b64}", "fps": 2.0},
                    {"type": "text", "text": query}
                ]
            }]
            try:
                response = self.client.chat_completion(messages=messages, max_tokens=500)
                results.append({"query": query, "answer": response.choices[0].message.content})
            except Exception as e:
                logger.error(f"Qwen3-VL Video Analysis failed: {e}")
                results.append({"query": query, "answer": f"Error: {e}"})
        return results

    # Stub implementations for text-only methods
    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0) -> str:
        # Qwen3-VL can also do text, but optimized for vision
        res = self.client.chat_completion(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}])
        return res.choices[0].message.content
        
    # ... (other required methods return defaults)
```

- [ ] **Step 3: Commit**
```bash
git add src/adapters/inference/qwen3_vl_adapter.py
git commit -m "feat: add Qwen3-VL-A3B SOTA video adapter"
```

---

### Task 2: Inject Adapter into Container

**Files:**
- Modify: `src/backend/animetix/containers.py`

- [ ] **Step 1: Add qwen3_vl_adapter property to Container**
```python
    @property
    def qwen3_vl_adapter(self):
        return self._get('qwen3_vl_adapter', lambda: Qwen3VLAdapter(token=os.getenv("HF_TOKEN")))
```

- [ ] **Step 2: Update video_quest_service to use it**
```python
    @property
    def video_quest_service(self):
        return self._get('video_quest_service', lambda: VideoQuestService(inference_engine=self.qwen3_vl_adapter))
```

- [ ] **Step 3: Commit**
```bash
git add src/backend/animetix/containers.py
git commit -m "chore: inject Qwen3-VL into VideoQuestService"
```

---

### Task 3: Enhance VideoQuestService Logic

**Files:**
- Modify: `src/core/domain/services/creative/video_quest.py`

- [ ] **Step 1: Implement "Guess the Episode" logic using Qwen3-VL**
Update `VideoQuestService` to use `localize_video_actions` for pinpointing episode numbers or key plot points.

- [ ] **Step 2: Commit**
```bash
git add src/core/domain/services/creative/video_quest.py
git commit -m "feat: implement episode guessing logic via Qwen3-VL"
```
