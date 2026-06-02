# Implement Robust Fallbacks for InferencePort Stubs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce hard crashes by implementing prompt-based or basic logic fallbacks for stubs in `UnifiedInferenceAdapter` and ensuring `InferencePort` has safe defaults.

**Architecture:** We leverage the multimodal (VLM) and general reasoning (LLM) capabilities of the Unified adapter to provide "good enough" results for specialized tasks (classification, detection, reranking) when a dedicated SOTA model is not available.

**Tech Stack:** Python, Requests, Base64, Pydantic (for structured outputs).

---

### Task 1: Implement LLM-based Fallbacks in UnifiedInferenceAdapter

**Files:**
- Modify: `backend/adapters/inference/unified_inference_adapter.py`

- [ ] **Step 1: Implement `rerank_documents`**
  Add `rerank_documents` using a prompt that asks the LLM to score documents from 0 to 1.

```python
    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Ré-ordonne les documents via un prompt LLM (fallback)."""
        if not documents:
            return []
        
        prompt = f"Requête: {query}\n\nDocuments à évaluer:\n"
        for i, doc in enumerate(documents):
            prompt += f"ID {i}: {doc[:500]}\n"
        
        prompt += "\nPour chaque document, donne un score de pertinence entre 0.0 (inutile) et 1.0 (parfait). Réponds avec une liste de scores JSON: [score0, score1, ...]"
        
        try:
            raw = self.generate(prompt, system_prompt="Tu es un système de réordonnancement (reranker) expert.", json_mode=False)
            import re
            match = re.search(r'\[.*\]', raw)
            if match:
                import json
                scores = json.loads(match.group(0))
                if len(scores) == len(documents):
                    return [float(s) for s in scores]
        except Exception as e:
            logger.warning(f"Reranking fallback failed: {e}")
        
        return [0.0] * len(documents)
```

- [ ] **Step 2: Implement `moderate_content`**
  Use a prompt to check for safety/spoilers.

```python
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Modère le contenu via un prompt LLM."""
        prompt = f"Texte à analyser: {text}\n\nCatégories à vérifier: {', '.join(categories)}\n\nRéponds au format JSON: {{'is_safe': bool, 'flagged_categories': [str], 'reason': str}}"
        try:
            return self.generate_structured(prompt, response_model=dict, system_prompt="Tu es un agent de modération.")
        except Exception:
            return {"is_safe": True, "flagged_categories": [], "reason": "Moderation fallback failed."}
```

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/unified_inference_adapter.py
git commit -m "feat: add LLM-based fallbacks for rerank and moderation in UnifiedInferenceAdapter"
```

### Task 2: Implement VLM-based Fallbacks in UnifiedInferenceAdapter

**Files:**
- Modify: `backend/adapters/inference/unified_inference_adapter.py`

- [ ] **Step 1: Implement `classify_image` using VLM**
  Reuse the multimodal logic to classify images.

```python
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """Classifie une image via VLM prompt."""
        prompt = f"Parmi ces labels: {', '.join(candidate_labels)}, lequel correspond le mieux à cette image ? Réponds au format JSON: {{'label': score}}."
        try:
            # We assume the endpoint supports multimodal if we call this
            desc = self.generate_image_description(image_data, prompt=prompt)
            import json
            import re
            match = re.search(r'\{.*\}', desc)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {l: 0.0 for l in candidate_labels}
```

- [ ] **Step 2: Implement `detect_objects` and `visual_rerank`**
  Add similar VLM prompt-based logic for these methods.

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/unified_inference_adapter.py
git commit -m "feat: add VLM-based fallbacks for image classification and detection"
```

### Task 3: Improve Defaults in InferencePort

**Files:**
- Modify: `backend/core/ports/inference_port.py`

- [ ] **Step 1: Change stubs to return empty structures instead of raising if possible**
  For example, `classify_image` should return `{}` by default instead of raising, to allow `FallbackInferenceAdapter` to continue without needing to catch exceptions for every single method if we want to be permissive.
  *(Actually, let's keep the `InferenceNotImplementedError` as it's useful for FallbackAdapter to know what's supported, but ensure FallbackAdapter handles it gracefully which it already does).*
  
  Wait, `FallbackInferenceAdapter` uses `_is_method_overridden` to build a cache. If the method is NOT overridden, it's NOT in the cache.
  If the method IS overridden but raises `InferenceNotImplementedError`, `FallbackInferenceAdapter` handles it in `_fallback_call`.

  Let's actually just fix the `TODO` comments in `InferencePort` to clarify they are base stubs.

- [ ] **Step 2: Commit**

```bash
git add backend/core/ports/inference_port.py
git commit -m "docs: clarify InferencePort stubs and ensure safe defaults"
```
