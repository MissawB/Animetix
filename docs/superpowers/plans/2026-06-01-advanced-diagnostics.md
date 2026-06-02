# Advanced Diagnostics & Uncertainty Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate from GPT-2 proxy-based uncertainty estimation to real logprobs extraction from inference engines (Ollama/BrainAPI), improving confidence scoring in the RAG workflow.

**Architecture:** Hexagonal architecture update. Migration from raw string returns to structured `InferenceResponse` objects in the `InferencePort` layer, with backward compatibility via a local proxy fallback.

**Tech Stack:** Python 3.11, Pydantic v2, Transformers (for local fallback), HTTTPX (BrainAPI).

---

### Task 1: Update Domain Schemas

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`
- Test: `tests/core/domain/test_ai_schemas.py`

- [ ] **Step 1: Write the failing test**
```python
def test_inference_response_schema():
    from backend.core.domain.entities.ai_schemas import InferenceResponse, TokenLogProb
    res = InferenceResponse(
        text="Luffy", 
        metadata={"logprobs": [{"token": "Luffy", "logprob": -0.01}]}
    )
    assert res.text == "Luffy"
    assert res.metadata.logprobs[0].token == "Luffy"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/core/domain/test_ai_schemas.py`

- [ ] **Step 3: Implement new Pydantic models**
```python
class TokenLogProb(BaseModel):
    token: str
    logprob: float
    top_logprobs: Optional[List[Dict[str, float]]] = None

class InferenceMetadata(BaseModel):
    logprobs: Optional[List[TokenLogProb]] = None
    usage: Optional[Dict[str, int]] = None
    thinking: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None

class InferenceResponse(BaseModel):
    text: str
    metadata: InferenceMetadata = Field(default_factory=lambda: InferenceMetadata())
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**
```bash
git add backend/core/domain/entities/ai_schemas.py
git commit -m "feat(domain): add InferenceResponse and metadata schemas"
```

### Task 2: Update InferencePort Interface

**Files:**
- Modify: `backend/core/ports/inference_port.py`

- [ ] **Step 1: Update signature of generate method**
```python
from ..entities.ai_schemas import InferenceResponse, InferenceMetadata

# Update generate method
def generate(
    self, 
    prompt: str, 
    system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
    thinking_budget: int = 0,
    thinking_mode: bool = False,
    include_logprobs: bool = False
) -> InferenceResponse:
    raise InferenceNotImplementedError("generate not implemented")
```

- [ ] **Step 2: Update signature of stream_generate**
```python
def stream_generate(
    self, 
    prompt: str, 
    system_prompt: str = "...",
    thinking_budget: int = 0,
    thinking_mode: bool = False,
    include_logprobs: bool = False
):
    raise InferenceNotImplementedError("stream_generate not implemented")
```

- [ ] **Step 3: Commit**
```bash
git add backend/core/ports/inference_port.py
git commit -m "refactor(port): update InferencePort to return InferenceResponse"
```

### Task 3: Update LLMService (The Consumer)

**Files:**
- Modify: `backend/core/domain/services/llm_service.py`

- [ ] **Step 1: Adapt generate method to handle InferenceResponse**
```python
# Change res = engine.generate(...) to:
response_obj = engine.generate(prompt, system_prompt, thinking_budget=thinking_budget, thinking_mode=thinking_mode)
res = response_obj.text
```

- [ ] **Step 2: Adapt usage logging to use response_obj.metadata.usage**

- [ ] **Step 3: Commit**
```bash
git add backend/core/domain/services/llm_service.py
git commit -m "refactor(service): adapt LLMService for InferenceResponse"
```

### Task 4: Support Logprobs in UnifiedInferenceAdapter

**Files:**
- Modify: `backend/adapters/inference/unified_inference_adapter.py`

- [ ] **Step 1: Update generate to return InferenceResponse**
- [ ] **Step 2: Implement logprobs extraction from Ollama/OpenAI response**
- [ ] **Step 3: Commit**
```bash
git add backend/adapters/inference/unified_inference_adapter.py
git commit -m "feat(adapter): support logprobs in UnifiedInferenceAdapter"
```

### Task 5: Support Logprobs in BrainAPIAdapter

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`

- [ ] **Step 1: Update generate to return InferenceResponse**
- [ ] **Step 2: Parse logprobs from BrainAPI response**
- [ ] **Step 3: Commit**
```bash
git add backend/adapters/inference/brain_api_adapter.py
git commit -m "feat(adapter): support real uncertainty in BrainAPIAdapter"
```

### Task 6: Update FallbackInferenceAdapter

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`

- [ ] **Step 1: Update generate and routing logic to handle InferenceResponse**
- [ ] **Step 2: Commit**
```bash
git add backend/adapters/inference/fallback_adapter.py
git commit -m "refactor(adapter): update FallbackInferenceAdapter for structured response"
```

### Task 7: Finalize UncertaintyService (Real Logprobs Logic)

**Files:**
- Modify: `backend/core/domain/services/xai_service.py`

- [ ] **Step 1: Update measure_confidence to use logprobs if present**
```python
def measure_confidence(self, prompt: str, completion: str, response: Optional[InferenceResponse] = None) -> Dict[str, Any]:
    if response and response.metadata.logprobs:
        # H = -sum(p * log(p))
        logprobs = [lp.logprob for lp in response.metadata.logprobs]
        import numpy as np
        probs = np.exp(logprobs)
        entropy = -np.mean(logprobs) # Approximate entropy from average logprob
        confidence_score = 1.0 - (entropy / 10.8) # Normalize
    else:
        # Fallback to GPT-2
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/domain/services/xai_service.py
git commit -m "feat(service): enable real logprobs uncertainty calculation"
```

### Task 8: Verification & Regression Testing

**Files:**
- Modify: `tests/adapters/test_inference_observability.py`

- [ ] **Step 1: Update tests for InferenceResponse return type**
- [ ] **Step 2: Run all tests**
```bash
pytest tests/adapters/test_inference_observability.py
```
- [ ] **Step 3: Commit**
```bash
git commit -m "test: verify advanced diagnostics and uncertainty"
```
