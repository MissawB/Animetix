# TransformersAdapter Deconstruction & Test Suite Repair Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deconstruct the monolithic `TransformersAdapter` into single-responsibility driven adapters (`TransformersTextAdapter` and `TransformersRerankAdapter`), update dependency injection registrations, and repair pre-existing test suite failures in video RAG and visual reranker modules.

**Architecture:** Split Text (Causal LM) and Rerank (Cross-Encoder) responsibilities into discrete classes, using original class as backward-compatible wrapper. Correct VLM tests to use `VisionTransformersAdapter`.

**Tech Stack:** Python 3.11, Pytest, dependency-injector, sentence_transformers, transformers.

---

### Task 1: Implement Standalone TransformersTextAdapter

**Files:**
- Create: `backend/adapters/inference/transformers_text_adapter.py`

- [ ] **Step 1: Write standalone Causal LM text adapter**
Create `backend/adapters/inference/transformers_text_adapter.py` with the dedicated text generation implementation:
```python
import logging
import os
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
transformers = lazy_import('transformers')
AutoModelForCausalLM = transformers.AutoModelForCausalLM
AutoTokenizer = transformers.AutoTokenizer

logger = logging.getLogger("animetix.inference.transformers_text")

class TransformersTextAdapter(InferencePort):
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.use_4bit = use_4bit

    def _load_model(self):
        if self.model: return
        try:
            from transformers import BitsAndBytesConfig
            logger.info(f"🏗️ Loading Local Model for Text: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            quantization_config = None
            if self.use_4bit:
                quantization_config = BitsAndBytesConfig(load_in_4bit=True)
                
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map="auto", 
                quantization_config=quantization_config,
                trust_remote_code=True
            )
        except Exception as e:
            logger.error(f"❌ Failed to load local text model: {e}")

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        try:
            self._load_model()
        except Exception as e:
            raise InferenceError(f"Critical failure during model loading: {str(e)}")
            
        if not self.model: 
            raise InferenceError("Local Transformers model not loaded.")
        
        try:
            if thinking_mode or thinking_budget > 0:
                prompt = f"<think>\nAnalyse en profondeur.\n</think>\n{prompt}"
                
            inputs = self.tokenizer(f"{system_prompt}\n\n{prompt}", return_tensors="pt").to(self.model.device)
            max_new_tokens = 512 + (thinking_budget if thinking_budget > 0 else 0)
            
            input_length = inputs.input_ids.shape[1]
            outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            generated_tokens = outputs[0][input_length:]
            return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        except Exception as e:
            raise InferenceError(f"Generation failed: {str(e)}")

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        try:
            yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)
        except InferenceError:
            raise

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
        found = [w for w in bad_words if w in text.lower()]
        is_safe = len(found) == 0
        return {
            "is_safe": is_safe,
            "detected_categories": found,
            "action": "block" if not is_safe else "allow"
        }

    def health_check(self) -> dict: 
        return {"status": "online" if self.model else "offline", "engine": "transformers_text"}
```

- [ ] **Step 2: Run a quick syntax check on the new file**
Run:
```powershell
python -m py_compile backend/adapters/inference/transformers_text_adapter.py
```
Expected: Compiles cleanly with no syntax errors.

- [ ] **Step 3: Commit**
```bash
git add backend/adapters/inference/transformers_text_adapter.py
git commit -m "feat: implement single-responsibility TransformersTextAdapter for text generation"
```

---

### Task 2: Implement Standalone TransformersRerankAdapter

**Files:**
- Create: `backend/adapters/inference/transformers_rerank_adapter.py`

- [ ] **Step 1: Write standalone cross-encoder document rerank adapter**
Create `backend/adapters/inference/transformers_rerank_adapter.py` with the dedicated reranking implementation:
```python
import logging
import os
from typing import List
from core.ports.inference_port import InferencePort
from core.utils.lazy_import import lazy_import

logger = logging.getLogger("animetix.inference.transformers_rerank")

class TransformersRerankAdapter(InferencePort):
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self._cross_encoder = None

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
            
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {cohere_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "rerank-multilingual-v3.0",
                    "query": query,
                    "documents": documents
                }
                response = requests.post("https://api.cohere.ai/v1/rerank", headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    scores = [0.0] * len(documents)
                    for item in data.get("results", []):
                        idx = item.get("index")
                        if idx is not None and idx < len(scores):
                            scores[idx] = float(item.get("relevance_score", 0.0))
                    return scores
            except Exception as e:
                logger.error(f"❌ Cohere Rerank API connection failed: {e}.")

        from core.utils.lazy_import import lazy_import
        sentence_transformers = lazy_import('sentence_transformers')
        
        if not self._cross_encoder:
            logger.info(f"🏗️ Loading CrossEncoder Model: {self.model_name}")
            self._cross_encoder = sentence_transformers.CrossEncoder(self.model_name)
            
        pairs = [[query, doc] for doc in documents]
        scores = self._cross_encoder.predict(pairs)
        return [float(score) for score in scores]

    def health_check(self) -> dict:
        return {"status": "online" if self._cross_encoder else "offline", "engine": "transformers_rerank"}
```

- [ ] **Step 2: Run a quick syntax check on the new file**
Run:
```powershell
python -m py_compile backend/adapters/inference/transformers_rerank_adapter.py
```
Expected: Compiles cleanly with no syntax errors.

- [ ] **Step 3: Commit**
```bash
git add backend/adapters/inference/transformers_rerank_adapter.py
git commit -m "feat: implement single-responsibility TransformersRerankAdapter for document reranking"
```

---

### Task 3: Refactor Compatibility Wrapper & DI Container

**Files:**
- Modify: `backend/adapters/inference/transformers_adapter.py`
- Modify: `backend/api/animetix/containers.py`
- Modify: `tests/core/test_inference_adapters.py`

- [ ] **Step 1: Refactor original transformers_adapter.py as a wrapper**
Open `backend/adapters/inference/transformers_adapter.py` and replace its contents with a clean deprecated compatibility wrapper class:
```python
import logging
from typing import List, Optional
from core.ports.inference_port import InferencePort
from .transformers_text_adapter import TransformersTextAdapter
from .transformers_rerank_adapter import TransformersRerankAdapter

logger = logging.getLogger("animetix.inference.transformers_legacy")

class TransformersAdapter(TransformersTextAdapter):
    """
    [DEPRECATED] Adaptateur monolithique d'origine pour Hugging Face.
    Conservé à des fins de compatibilité descendante.
    """
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True):
        super().__init__(model_id, use_4bit)
        self._rerank_adapter = TransformersRerankAdapter()

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        logger.warning("⚠️ Call to deprecated method 'rerank_documents' on legacy 'TransformersAdapter'. Please use 'TransformersRerankAdapter' instead.")
        return self._rerank_adapter.rerank_documents(query, documents)

    def health_check(self) -> dict:
        status_text = super().health_check()
        return {"status": status_text.get("status", "offline"), "engine": "transformers_legacy"}
```

- [ ] **Step 2: Update containers.py to register new standalone singletons**
Open `backend/api/animetix/containers.py` and register the new standalone classes:
- Add imports around line 107:
```python
from adapters.inference.transformers_text_adapter import TransformersTextAdapter
from adapters.inference.transformers_rerank_adapter import TransformersRerankAdapter
```
- Define new providers around line 178:
```python
    transformers_text_adapter = providers.Singleton(
        TransformersTextAdapter,
        model_id="Qwen/Qwen2.5-1.5B-Instruct",
        use_4bit=True
    )

    transformers_rerank_adapter = providers.Singleton(
        TransformersRerankAdapter
    )
```
- Update `inference_engine`'s list around line 208 to include the new standalone adapters:
```python
    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            unified_inference_adapter,
            transformers_text_adapter,
            transformers_rerank_adapter,
            gguf_adapter,
            diffusers_adapter,
            vision_transformers_adapter,
            audio_transformers_adapter,
            moondream_adapter,
            manga_ocr_adapter,
            providers.Factory(
                VllmAdapter,
                api_base=os.getenv("VLLM_API_BASE", "http://vllm:8000/v1"),
                model_name="meta-llama/Llama-3-8B-Instruct"
            ),
            providers.Factory(
                BrainAPIAdapter,
                brain_api_url=os.getenv("BRAIN_API_URL", "")
            )
        ),
        obs_service=obs_service
    )
```

- [ ] **Step 3: Update core test_inference_adapters.py to test new adapters**
Modify `tests/core/test_inference_adapters.py` to add validation assertions for the new standalone text and rerank classes:
- Add imports at the beginning of the file:
```python
from backend.adapters.inference.transformers_text_adapter import TransformersTextAdapter
from backend.adapters.inference.transformers_rerank_adapter import TransformersRerankAdapter
```
- Add a new test case validating the split:
```python
def test_transformers_text_and_rerank_adapters_instantiation():
    text_adapter = TransformersTextAdapter(model_id="fake/id")
    assert text_adapter.model_id == "fake/id"
    
    rerank_adapter = TransformersRerankAdapter()
    assert rerank_adapter.model_name is not None
```

- [ ] **Step 4: Run core inference tests to verify they all pass**
Run:
```powershell
pytest tests/core/test_inference_adapters.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/adapters/inference/transformers_adapter.py backend/api/animetix/containers.py tests/core/test_inference_adapters.py
git commit -m "refactor: wrap legacy transformers adapter and register new standalone text/rerank singletons in DI"
```

---

### Task 4: Repair Misconfigured Video RAG and Visual Rerank Tests

**Files:**
- Modify: `tests/adapters/test_video_rag.py`
- Modify: `tests/adapters/test_visual_reranker.py`

- [ ] **Step 1: Fix test_video_rag.py to use VisionTransformersAdapter**
Open `tests/adapters/test_video_rag.py` and modify imports and mocks:
- Replace `TransformersAdapter` imports with `VisionTransformersAdapter`:
```python
from adapters.inference.vision_transformers_adapter import VisionTransformersAdapter
```
- Update fixtures:
```python
@pytest.fixture
def adapter():
    return VisionTransformersAdapter(use_4bit=False)
```
- Replace all `@patch("adapters.inference.transformers_adapter.TransformersAdapter._load_video_vlm", MagicMock())` patches with:
```python
@patch("adapters.inference.vision_transformers_adapter.VisionTransformersAdapter._load_video_vlm", MagicMock())
```
- Replace `@patch("adapters.inference.transformers_adapter.TransformersAdapter._load_video_vlm", MagicMock())` at line 43 and line 63.

- [ ] **Step 2: Fix test_visual_reranker.py to use VisionTransformersAdapter**
Open `tests/adapters/test_visual_reranker.py` and modify imports:
- Replace `TransformersAdapter` imports with `VisionTransformersAdapter`:
```python
from backend.adapters.inference.vision_transformers_adapter import VisionTransformersAdapter
```
- Replace instantiation `adapter = TransformersAdapter()` with `adapter = VisionTransformersAdapter()` on line 35 and line 53.

- [ ] **Step 3: Run the corrected test files using pytest and ensure they pass cleanly**
Run:
```powershell
pytest tests/adapters/test_video_rag.py tests/adapters/test_visual_reranker.py -v
```
Expected: PASS (exit code 0).

- [ ] **Step 4: Commit**
```bash
git add tests/adapters/test_video_rag.py tests/adapters/test_visual_reranker.py
git commit -m "test: correct video RAG and visual reranker tests to import and use VisionTransformersAdapter"
```
