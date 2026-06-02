# Thinking Mode Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit `thinking_mode: bool = False` flag to the inference pipeline to leverage Qwen3-4B-Instruct's dual-mode reasoning.

**Architecture:** Update `InferencePort` (interface), `LLMService` (domain), and concrete adapters (infrastructure) to support the new flag.

**Tech Stack:** Python, vLLM, llama-cpp-python, Agentic RAG.

---

### Task 1: Update InferencePort Interface

**Files:**
- Modify: `backend/core/ports/inference_port.py`

- [ ] **Step 1: Update `generate` and `stream_generate` signatures**

```python
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False  # Added
    ) -> str:
        pass

    @abstractmethod
    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False  # Added
    ):
        pass
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/ports/inference_port.py
git commit -m "feat: add thinking_mode to InferencePort"
```

---

### Task 2: Update LLMService Domain Logic

**Files:**
- Modify: `backend/core/domain/services/llm_service.py`

- [ ] **Step 1: Update `generate` and `ask_oracle_stream` to pass `thinking_mode`**

```python
    def generate(self, prompt: str, system_prompt: str = "", forbidden_terms: list = None, use_slm: bool = False, thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        # ...
        res = engine.generate(prompt, system_prompt, thinking_budget=thinking_budget, thinking_mode=thinking_mode)
```

- [ ] **Step 2: Update `ask_oracle_stream`**

```python
    def ask_oracle_stream(self, media_type: str, title: str, question: str, thinking_mode: bool = False):
        # ...
        yield from self.inference_engine.stream_generate(prompt, system, thinking_mode=thinking_mode)
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/llm_service.py
git commit -m "feat: propagate thinking_mode in LLMService"
```

---

### Task 3: Update Primary Adapters (Vllm & Gguf)

**Files:**
- Modify: `backend/adapters/inference/vllm_adapter.py`
- Modify: `backend/adapters/inference/gguf_adapter.py`

- [ ] **Step 1: Update `VllmAdapter` to pass `thinking_mode` in payload**

```python
    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        # ...
        res = requests.post(..., json={
            "model": self.model_name,
            "messages": [...],
            "thinking_budget": thinking_budget,
            "thinking_mode": thinking_mode  # Added
        }, ...)
```

- [ ] **Step 2: Update `GgufAdapter` to handle `thinking_mode`**

```python
    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        # ...
        if thinking_mode:
            system_prompt = f"{system_prompt}\n<think>\nActive ton raisonnement approfondi pour cette requête.\n</think>"
        # ...
```

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/vllm_adapter.py backend/adapters/inference/gguf_adapter.py
git commit -m "feat: implement thinking_mode in Vllm and Gguf adapters"
```

---

### Task 4: Update Fallback and Auxiliary Adapters

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`
- Modify: `backend/adapters/inference/brain_api_adapter.py`
- Modify: `backend/adapters/inference/transformers_adapter.py`
- Modify: `backend/adapters/inference/local_llama_adapter.py`

- [ ] **Step 1: Update `FallbackInferenceAdapter` to propagate flag**

- [ ] **Step 2: Update signatures in all other adapters to match interface**

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/*.py
git commit -m "feat: finalize thinking_mode support across all adapters"
```

---

### Task 5: Integration in AgenticRAGService

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`

- [ ] **Step 1: Enable `thinking_mode` for high complexity queries**

```python
    def plan_and_solve_stream(self, query: str, media_type: str, user_id: Optional[str] = None) -> Generator[Dict, None, None]:
        thinking_budget, complexity = self._assess_complexity(query)
        thinking_mode = complexity >= 2  # Enable for complex tasks
        # ...
        plan = self.planner.plan(query, memories, thinking_budget=thinking_budget // 2, thinking_mode=thinking_mode)
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/agentic_rag_service.py
git commit -m "feat: enable thinking_mode for complex queries in AgenticRAG"
```
