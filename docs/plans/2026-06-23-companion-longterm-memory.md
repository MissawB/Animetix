# Connect long-term memory to the AI companion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing `LongTermMemoryService` into the companion flow — retrieve relevant memories into the prompt, and persist turns evicted from the 5-turn session window — without adding request latency or breaking on failure.

**Architecture:** `CompanionService` gains an optional `memory_service`: `generate_response` retrieves memories and passes them as a new `{memories}` prompt slot; `remember()` persists evicted turns in a daemon thread. The 3 personality templates get the `{memories}` slot; the companion view passes `user_id` and hands evicted turns to `remember()`; DI injects `memory_service`.

**Tech Stack:** Python 3.12, Django/DRF, dependency-injector, pytest, `threading`, YAML prompt templates.

## Global Constraints

- Behavior-preserving for the no-memory path: with no `user_id` or no `memory_service`, retrieve and remember are no-ops; existing companion behavior/tests stay green.
- Persistence runs in a daemon thread and never affects the response; `store_memory` already swallows its own errors.
- `PromptManager.get_prompt` uses `template.format(**kwargs)`: extra kwargs are ignored, but a `{memories}` placeholder with no `memories` kwarg raises `KeyError`. Therefore the service change (Task 1, always passes `memories`) MUST land before the template change (Task 2). The only caller of the 3 personality templates is `CompanionService.generate_response`.
- All tests mock the LLM / vector store / threading — CI-safe.
- Spec: `docs/specs/2026-06-23-companion-longterm-memory-design.md`.

---

### Task 1: CompanionService — retrieve memories + remember()

**Files:**
- Modify: `backend/core/domain/services/companion_service.py` (imports; `__init__`; `generate_response`; add `remember`)
- Test: `tests/core/test_companion_memory.py`

**Interfaces:**
- Produces: `CompanionService(llm_service, prompt_manager, memory_service=None)`;
  `generate_response(mentor_id, user_msg, context="", history=None, user_id=None) -> str` (now also passes a `memories=` kwarg to `get_prompt`); `remember(user_id, turns) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_companion_memory.py
from unittest.mock import MagicMock, patch

from core.domain.services.companion_service import CompanionService


def _svc(memory_service=None):
    pm = MagicMock()
    pm.get_prompt.return_value = ("p", "s")
    llm = MagicMock()
    llm.generate.return_value = "resp"
    return CompanionService(llm, pm, memory_service=memory_service), pm


def test_generate_injects_retrieved_memories():
    mem = MagicMock()
    mem.retrieve_relevant_memories.return_value = "past: likes Naruto"
    svc, pm = _svc(mem)
    svc.generate_response("sensei", "hi", user_id="u1")
    mem.retrieve_relevant_memories.assert_called_once_with("u1", "hi")
    assert pm.get_prompt.call_args.kwargs["memories"] == "past: likes Naruto"


def test_generate_no_memories_without_user_id():
    mem = MagicMock()
    svc, pm = _svc(mem)
    svc.generate_response("sensei", "hi")
    mem.retrieve_relevant_memories.assert_not_called()
    assert pm.get_prompt.call_args.kwargs["memories"] == ""


def test_generate_no_memories_without_memory_service():
    svc, pm = _svc(None)
    svc.generate_response("sensei", "hi", user_id="u1")
    assert pm.get_prompt.call_args.kwargs["memories"] == ""


def test_remember_stores_evicted_turns():
    mem = MagicMock()
    svc, _ = _svc(mem)
    turns = [{"role": "user", "content": "old"}]

    def run_sync(target, args, daemon):
        target(*args)
        return MagicMock()

    with patch(
        "core.domain.services.companion_service.threading.Thread",
        side_effect=run_sync,
    ):
        svc.remember("u1", turns)
    mem.store_memory.assert_called_once_with("u1", turns)


def test_remember_is_noop_without_turns_user_or_service():
    mem = MagicMock()
    svc, _ = _svc(mem)
    svc.remember("u1", [])            # no turns
    svc.remember(None, [{"x": 1}])    # no user
    CompanionService(MagicMock(), MagicMock(), None).remember("u1", [{"x": 1}])  # no service
    mem.store_memory.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/core/test_companion_memory.py -q`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'memory_service'` (and `remember` missing).

- [ ] **Step 3: Write the implementation**

In `backend/core/domain/services/companion_service.py`, add `import threading` at the top (with the other imports), and apply:

```python
    def __init__(self, llm_service, prompt_manager, memory_service=None):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.memory_service = memory_service
```

In `generate_response`, add `user_id=None` to the signature and retrieve memories before building the prompt:

```python
    def generate_response(
        self,
        mentor_id: str,
        user_msg: str,
        context: str = "",
        history: Optional[List[dict]] = None,
        user_id: Optional[str] = None,
    ) -> str:
```

and (keeping the existing `history_str` build) change the `get_prompt` call to:

```python
        memories = ""
        if self.memory_service and user_id:
            memories = self.memory_service.retrieve_relevant_memories(user_id, user_msg)

        prompt, system = self.prompt_manager.get_prompt(
            prompt_id,
            user_msg=self._sanitize_and_delimit(user_msg, "user_input"),
            context=self._sanitize_and_delimit(context, "context"),
            history=history_str,
            memories=memories,
        )
```

Add the `remember` method (e.g. after `generate_response`, before `_sanitize_and_delimit`):

```python
    def remember(self, user_id, turns) -> None:
        """Persist evicted conversation turns into long-term memory, in the background."""
        if not (self.memory_service and user_id and turns):
            return
        threading.Thread(
            target=self.memory_service.store_memory,
            args=(user_id, turns),
            daemon=True,
        ).start()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/core/test_companion_memory.py tests/core/test_companion_service.py -q`
Expected: PASS (the new file's 5 tests AND the existing companion-service tests — the extra `memories` kwarg does not break their per-key assertions).

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/companion_service.py tests/core/test_companion_memory.py
git commit -m "feat(companion): retrieve long-term memories + background remember()"
```

---

### Task 2: Add the {memories} slot to the 3 personality templates

**Files:**
- Modify: `backend/core/domain/services/prompts/prompts.yaml` (sensei/tsundere/kuudere templates)
- Test: `tests/core/test_companion_prompts_memory.py`

**Interfaces:**
- Consumes: `generate_response` now passes `memories=` (Task 1), so the placeholder is always filled.
- Produces: each personality template renders a `SOUVENIRS PERTINENTS :` section from `{memories}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_companion_prompts_memory.py
import os

from core.domain.services.prompt_manager import PromptManager

PROMPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "backend", "core", "domain", "services", "prompts",
    )
)


def test_personality_templates_render_with_memories():
    pm = PromptManager(prompts_dir=PROMPTS_DIR)
    for key in ("sensei_personality", "tsundere_personality", "kuudere_personality"):
        prompt, _ = pm.get_prompt(
            key, user_msg="u", context="c", history="h", memories="MY-MEMORY"
        )
        assert "MY-MEMORY" in prompt, f"{key} did not render the memories slot"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/core/test_companion_prompts_memory.py -q`
Expected: FAIL — `AssertionError: sensei_personality did not render the memories slot` (no `{memories}` placeholder yet, so the extra kwarg is ignored).

- [ ] **Step 3: Edit the three templates**

In `backend/core/domain/services/prompts/prompts.yaml`, apply these three edits (each inserts a `SOUVENIRS PERTINENTS :` block between the `{history}` block and the `MISSION :` line; the 4-space indentation must match the surrounding block scalar).

Edit 1 (sensei) — replace:

```
    {history}


    MISSION : Réponds en tant que Sensei sage, calme et encourageant.
```

with:

```
    {history}


    SOUVENIRS PERTINENTS :

    {memories}


    MISSION : Réponds en tant que Sensei sage, calme et encourageant.
```

Edit 2 (tsundere) — replace:

```
    {history}


    MISSION : Réponds en tant que personnage Tsundere.
```

with:

```
    {history}


    SOUVENIRS PERTINENTS :

    {memories}


    MISSION : Réponds en tant que personnage Tsundere.
```

Edit 3 (kuudere) — replace:

```
    {history}


    MISSION : Réponds en tant que personnage Kuudere.
```

with:

```
    {history}


    SOUVENIRS PERTINENTS :

    {memories}


    MISSION : Réponds en tant que personnage Kuudere.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/core/test_companion_prompts_memory.py -q`
Expected: PASS (1 passed — all three render `MY-MEMORY`, no `KeyError`).

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/prompts/prompts.yaml tests/core/test_companion_prompts_memory.py
git commit -m "feat(companion): add {memories} slot to the 3 personality prompts"
```

---

### Task 3: Wire DI + view eviction → remember

**Files:**
- Modify: `backend/api/animetix/containers/core_services.py` (companion_service provider, lines 95-99)
- Modify: `backend/api/animetix/api/companion.py` (the `generate_response` call ~60-65; the truncation block ~89-91)
- Test: `tests/api/test_companion.py` (add a view test) + `tests/backend/test_companion_di.py` (new, DI wiring)

**Interfaces:**
- Consumes: `CompanionService.remember` (Task 1); `agentic.memory_service`.
- Produces: the companion view persists evicted turns; the DI provides `memory_service` to `companion_service`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/api/test_companion.py`:

```python
def test_companion_evicts_and_remembers_when_over_five_turns():
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/companion/interact/",
        {"mentor_id": "sensei", "user_message": "Hello", "context_url": ""},
        content_type="application/json",
    )
    user = MagicMock()
    user.id = 1
    user.tier = "free"
    user.is_authenticated = True
    request.user = user
    prior = [{"role": "user", "content": f"old{i}"} for i in range(4)]
    request.session = {"companion_history": list(prior)}

    with (
        patch("backend.api.animetix.api.companion.get_container") as mock_get_container,
        patch("animetix.api.billing.deduct_berrix"),
    ):
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "hi back"
        mock_container.core.companion_service.return_value = mock_service
        mock_guard = MagicMock()
        mock_guard.validate_input.return_value = {"is_safe": True}
        mock_guard.validate_output.return_value = {"is_safe": True}
        mock_container.core.guardrail_service.return_value = mock_guard
        mock_container.infrastructure.usage_port.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        from rest_framework.test import force_authenticate  # noqa: E402

        view = CompanionInteractView.as_view(permission_classes=[])
        force_authenticate(request, user=user)
        response = view(request)

    assert response.status_code == 200
    # the window keeps the last 5 turns
    assert len(response.data["history"]) == 5
    # the single evicted turn was handed to long-term memory
    mock_service.remember.assert_called_once()
    args = mock_service.remember.call_args.args
    assert args[0] == 1 and args[1] == [prior[0]]
    # generate_response was given the user id for retrieval
    assert mock_service.generate_response.call_args.kwargs["user_id"] == 1
```

Create `tests/backend/test_companion_di.py`:

```python
def test_companion_service_provider_wires_memory_service():
    from animetix.containers import get_container

    provider = get_container().core.companion_service
    assert "memory_service" in provider.kwargs
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/api/test_companion.py::test_companion_evicts_and_remembers_when_over_five_turns tests/backend/test_companion_di.py -q`
Expected: FAIL — the view never calls `remember` / passes `user_id`; the provider has no `memory_service` kwarg.

- [ ] **Step 3: Apply the DI + view edits**

In `backend/api/animetix/containers/core_services.py`, change the `companion_service` provider to:

```python
    companion_service = providers.Singleton(
        LazyClass("core.domain.services.companion_service", "CompanionService"),
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager,
        memory_service=agentic.memory_service,
    )
```

In `backend/api/animetix/api/companion.py`, add `user_id` to the call:

```python
            response_text = companion_service.generate_response(
                mentor_id=mentor_id,
                user_msg=user_message,
                context=context_url,
                history=history,
                user_id=request.user.id,
            )
```

and replace the truncation block:

```python
            # Keep only last 5 entries
            if len(history) > 5:
                history = history[-5:]
```

with:

```python
            # Persist turns evicted from the 5-turn window into long-term memory,
            # then keep only the last 5.
            if len(history) > 5:
                evicted = history[:-5]
                companion_service.remember(request.user.id, evicted)
                history = history[-5:]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/api/test_companion.py tests/backend/test_companion_di.py -q`
Expected: PASS (the new view test, the new DI test, and the existing `test_companion_interact_view_*` — the latter starts with an empty session so no eviction, and its mocked `generate_response` tolerates the extra `user_id` kwarg).

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/containers/core_services.py backend/api/animetix/api/companion.py tests/api/test_companion.py tests/backend/test_companion_di.py
git commit -m "feat(companion): wire memory_service via DI + persist evicted turns from the view"
```

---

### Task 4: Verification sweep

**Files:**
- Verify only (no new product code).

- [ ] **Step 1: Run the companion + prompt suites**

Run: `python -m pytest tests/core/test_companion_memory.py tests/core/test_companion_service.py tests/core/test_companion_prompts_memory.py tests/api/test_companion.py tests/api/test_companion_api.py tests/backend/test_companion_di.py -q -p no:cacheprovider`
Expected: PASS (all). If any previously-passing test newly fails, fix the cause (do not weaken the test) and re-run.

- [ ] **Step 2: Lint**

Run: `python -m ruff check backend/core/domain/services/companion_service.py backend/api/animetix/api/companion.py backend/api/animetix/containers/core_services.py`
Run: `python -m ruff format backend/core/domain/services/companion_service.py backend/api/animetix/api/companion.py backend/api/animetix/containers/core_services.py tests/core/test_companion_memory.py tests/core/test_companion_prompts_memory.py tests/api/test_companion.py tests/backend/test_companion_di.py`
Expected: All checks passed; format clean.

- [ ] **Step 3: Commit (only if ruff format changed files)**

```bash
git add -A
git commit -m "style: ruff format for companion long-term memory"
```

---

## Notes for the executor

- Do NOT change `LongTermMemoryService`, the 5-turn window size, or the memory store.
- `episodic_memory_compressor` + Neo4j linking and summarization batching are explicit follow-ups, not part of this plan.
- `store_memory` already guards its own failures; `remember` just runs it off the request thread.
