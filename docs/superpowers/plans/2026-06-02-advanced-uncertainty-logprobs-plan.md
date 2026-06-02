# Advanced Uncertainty Logprobs Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate uncertainty calculations (entropy, perplexity) from local text-based proxy evaluations to real logprob execution when exposed by the Ollama and BrainAPI adapters.

**Architecture:** We use a Cache-based approach (Approach A). The adapters retrieve real `logprobs` from their endpoints by default and cache them alongside the completion. When `calculate_uncertainty` is called on the same generated completion, we extract and compute the exact Shannon entropy, perplexity, and confidence in O(1) directly from the cached logprobs.

**Tech Stack:** Python, Numpy, Pytest, Pydantic, HTTPX

---

### Task 1: Interface Compliance for Local Motes

**Files:**
- Modify: `backend/adapters/inference/local_text_adapter.py:36-38`
- Modify: `backend/adapters/inference/qwen3_vl_adapter.py:37-39`

- [ ] **Step 1: Update LocalTextAdapter.generate signature**
  Modify [local_text_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/local_text_adapter.py) around line 36 to accept `include_logprobs` and `**kwargs`.
  ```python
      def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False, include_logprobs: bool = False, **kwargs) -> str:
  ```

- [ ] **Step 2: Update Qwen3VLAdapter.generate signature**
  Modify [qwen3_vl_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/qwen3_vl_adapter.py) around line 37 to accept `include_logprobs` and `**kwargs`.
  ```python
      def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False, include_logprobs: bool = False, **kwargs) -> str:
  ```

- [ ] **Step 3: Run existing unit tests**
  Run: `pytest tests/adapters/test_inference_observability.py -v`
  Expected: All existing observability tests pass successfully.

---

### Task 2: UnifiedInferenceAdapter Caching & Uncertainty Calculation

**Files:**
- Modify: `backend/adapters/inference/unified_inference_adapter.py`

- [ ] **Step 1: Initialize cache attributes**
  In [unified_inference_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/unified_inference_adapter.py) constructor `__init__`, add:
  ```python
          self._last_completion = None
          self._last_logprobs = None
  ```

- [ ] **Step 2: Store cache during generate**
  In [unified_inference_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/unified_inference_adapter.py) method `generate()`, store the generated text and extracted logprobs in the cache before returning the `InferenceResponse`:
  ```python
                  self._last_completion = raw_content
                  self._last_logprobs = parsed_logprobs
                  return InferenceResponse(
                      text=raw_content,
                      metadata=InferenceMetadata(
                          logprobs=parsed_logprobs,
                          usage=usage
                      )
                  )
  ```

- [ ] **Step 3: Store cache during stream_generate**
  In `stream_generate()` chunk loop:
  ```python
                                      if 'content' in delta:
                                          self._last_completion = (self._last_completion or "") + delta['content']
                                          if parsed_logprobs:
                                              if self._last_logprobs is None:
                                                  self._last_logprobs = []
                                              self._last_logprobs.extend(parsed_logprobs)
  ```

- [ ] **Step 4: Update calculate_uncertainty to use cache**
  In `calculate_uncertainty()`:
  ```python
      def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
          """Calcule la certitude mathématique réelle (entropie, perplexité) d'une génération."""
          try:
              # Check if we have cached real logprobs for this completion
              if getattr(self, "_last_completion", None) == completion and getattr(self, "_last_logprobs", None):
                  logprobs = [lp.logprob for lp in self._last_logprobs if lp.logprob is not None]
                  if logprobs:
                      avg_entropy = -sum(logprobs) / len(logprobs)
                      confidence = max(0.0, min(1.0, 1.0 - (avg_entropy / 10.8)))
                      perplexity = float(np.exp(avg_entropy))
                      logger.info("📊 UnifiedInferenceAdapter: Using real logprobs from cache.")
                      return {
                          "entropy": round(avg_entropy, 4),
                          "perplexity": round(perplexity, 4),
                          "confidence": round(confidence, 4)
                      }
              
              # Fallback to local GPT-2
              model, tokenizer, torch = _get_evaluation_resources()
              # ... rest of existing code ...
  ```

---

### Task 3: BrainAPIAdapter Caching & Uncertainty Calculation

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`

- [ ] **Step 1: Initialize cache attributes**
  In [brain_api_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/brain_api_adapter.py) constructor `__init__`, add:
  ```python
          self._last_completion = None
          self._last_logprobs = None
  ```

- [ ] **Step 2: Store cache during generate**
  In `generate()`, store the generated text and extracted logprobs in the cache:
  ```python
                  self._last_completion = text
                  self._last_logprobs = parsed_logprobs
  ```

- [ ] **Step 3: Update calculate_uncertainty to use cache**
  In `calculate_uncertainty()`:
  ```python
      def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
          try:
              if getattr(self, "_last_completion", None) == completion and getattr(self, "_last_logprobs", None):
                  logprobs = [lp.logprob for lp in self._last_logprobs if lp.logprob is not None]
                  if logprobs:
                      import numpy as np
                      avg_entropy = -sum(logprobs) / len(logprobs)
                      confidence = max(0.0, min(1.0, 1.0 - (avg_entropy / 10.8)))
                      perplexity = float(np.exp(avg_entropy))
                      logger.info("📊 BrainAPIAdapter: Using real logprobs from cache.")
                      return {
                          "entropy": round(avg_entropy, 4),
                          "perplexity": round(perplexity, 4),
                          "confidence": round(confidence, 4)
                      }
              
              # Fallback to HTTP POST /uncertainty
              if not self.brain_api_url: return {}
              # ... rest of existing code ...
  ```

---

### Task 4: FallbackInferenceAdapter Caching & Caching Propagation

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`

- [ ] **Step 1: Initialize cache attributes**
  In [fallback_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/fallback_adapter.py) constructor `__init__`, add:
  ```python
          self._last_completion = None
          self._last_logprobs = None
  ```

- [ ] **Step 2: Store cache during generate**
  In `generate()`, update cache from successfully generated response:
  ```python
                  self._last_completion = result.text
                  self._last_logprobs = result.metadata.logprobs if result.metadata else None
                  return result
  ```

- [ ] **Step 3: Update calculate_uncertainty**
  In `calculate_uncertainty()`, check FallbackInferenceAdapter cache first:
  ```python
      def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
          if getattr(self, "_last_completion", None) == completion and getattr(self, "_last_logprobs", None):
              logprobs = [lp.logprob for lp in self._last_logprobs if lp.logprob is not None]
              if logprobs:
                  import numpy as np
                  avg_entropy = -sum(logprobs) / len(logprobs)
                  confidence = max(0.0, min(1.0, 1.0 - (avg_entropy / 10.8)))
                  perplexity = float(np.exp(avg_entropy))
                  logger.info("📊 FallbackInferenceAdapter: Using real logprobs from cache.")
                  return {
                      "entropy": round(avg_entropy, 4),
                      "perplexity": round(perplexity, 4),
                      "confidence": round(confidence, 4)
                  }
          return self._fallback_call("calculate_uncertainty", prompt, completion) or {}
  ```

---

### Task 5: Enable Logprobs in LLMService

**Files:**
- Modify: `backend/core/domain/services/llm_service.py`

- [ ] **Step 1: Pass include_logprobs=True in generate**
  Modify [llm_service.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/llm_service.py) around line 69:
  ```python
              response_obj = engine.generate(
                  prompt, 
                  system_prompt, 
                  thinking_budget=thinking_budget, 
                  thinking_mode=thinking_mode,
                  include_logprobs=True
              )
  ```

---

### Task 6: Unit Testing & Completion Validation

**Files:**
- Modify: `tests/adapters/test_inference_observability.py`
- Modify: `docs/TODO.md`

- [ ] **Step 1: Add a test case for real logprobs caching**
  Add a new test inside [test_inference_observability.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/adapters/test_inference_observability.py) verifying the cache logic and calculation correctness.
  ```python
  def test_unified_uncertainty_cache():
      from core.domain.entities.ai_schemas import TokenLogProb
      adapter = UnifiedInferenceAdapter()
      adapter._last_completion = "Test answer"
      adapter._last_logprobs = [
          TokenLogProb(token="Test", logprob=-0.5),
          TokenLogProb(token="answer", logprob=-0.2)
      ]
      res = adapter.calculate_uncertainty("prompt", "Test answer")
      assert res["confidence"] > 0.9
      assert res["entropy"] == pytest.approx(0.35)
  ```

- [ ] **Step 2: Run all tests**
  Run: `pytest tests/adapters/test_inference_observability.py tests/core/test_xai_service.py -v`
  Expected: PASS

- [ ] **Step 3: Update TODO.md**
  Modify [TODO.md](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/docs/TODO.md) to check off the diagnostics task:
  ```diff
  - - [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
  + - [x] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
  ```
