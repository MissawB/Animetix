# Design — Connect long-term memory to the AI companion

**Date:** 2026-06-23
**Status:** Approved (approach A)
**TODO source:** "Backend — companion n'exploite pas la mémoire long-terme — keeps only 5 session turns while `long_term_memory_service` exists and isn't wired."

## Problem

The companion endpoint keeps only the last 5 conversation turns in the Django session
(`backend/api/animetix/api/companion.py`) and discards older turns silently. A working
`LongTermMemoryService` already exists (on pgvector) with `retrieve_relevant_memories(user_id,
query)` and `store_memory(user_id, history)`, but the companion never calls it. So the companion
has no memory beyond the last 5 turns.

This work wires the existing memory service into the companion flow: **retrieve** relevant past
memories into the prompt, and **persist** turns evicted from the 5-turn window into long-term
memory (so the memory actually fills up from companion use).

## Current state (verified)

- `CompanionService.generate_response(mentor_id, user_msg, context="", history=None) -> str`
  (`backend/core/domain/services/companion_service.py`) builds the prompt from `user_msg`,
  `context`, `history`; it has no `user_id` and never touches memory. Constructor:
  `(llm_service, prompt_manager)`.
- `LongTermMemoryService` (`backend/core/domain/services/long_term_memory_service.py`):
  `retrieve_relevant_memories(user_id, current_query, limit=3) -> str` (vector query, guarded,
  returns "" on failure); `store_memory(user_id, conversation_history)` (LLM-summarizes the history
  then upserts to pgvector, guarded). Wired in DI as `agentic.memory_service`.
- The companion view keeps `history` in `request.session["companion_history"]`, appends
  `{"role","content"}` turns, then truncates `history = history[-5:]` (the eviction point).
- The 3 personality prompt templates (`sensei_personality`, `tsundere_personality`,
  `kuudere_personality` in `prompts.yaml`) expose `{user_msg}`, `{context}`, `{history}` — no memory
  slot.
- DI: `companion_service` provider (`containers/core_services.py:95`) takes `llm_service`,
  `prompt_manager`; `agentic.memory_service` exists and is injectable.
- Existing companion tests (`tests/core/test_companion_service.py`, `tests/api/test_companion*.py`)
  call `generate_response` and assert `get_prompt` was called with `user_msg`/`context`/`history`.

## Goals / non-goals

**Goals**
1. The companion retrieves relevant long-term memories and includes them in the prompt.
2. Turns evicted from the 5-turn session window are persisted to long-term memory.
3. Persistence adds no request latency (background thread) and never breaks the response on failure.
4. Backward compatible: existing companion behavior/tests stay green when no `user_id`/memory.

**Non-goals**
- `episodic_memory_compressor` + Neo4j profile linking (follow-up).
- Changing the 5-turn window size, the memory store, or `LongTermMemoryService`'s internals.

## Design (approach A)

### 1. CompanionService (modified)

- `__init__(self, llm_service, prompt_manager, memory_service=None)` — `memory_service` optional so
  existing constructions keep working.
- `generate_response(self, mentor_id, user_msg, context="", history=None, user_id=None) -> str`:
  - `memories = ""`; if `self.memory_service and user_id:`
    `memories = self.memory_service.retrieve_relevant_memories(user_id, user_msg)`.
  - pass `memories=memories` to `self.prompt_manager.get_prompt(prompt_id, user_msg=..., context=...,
    history=..., memories=...)` (new kwarg).
- `remember(self, user_id, turns) -> None`: if `self.memory_service and user_id and turns`, start a
  detached thread (`threading.Thread(target=self.memory_service.store_memory, args=(user_id, turns),
  daemon=True).start()`) — mirrors the agentic-RAG `sync_user_interaction` background pattern. No-op
  otherwise. Persistence failures are already swallowed inside `store_memory`.

### 2. Prompts (prompts.yaml)

Add a labelled block to each of the 3 personality templates, e.g. after the `HISTORIQUE` block:

```
SOUVENIRS PERTINENTS :
{memories}
```

An empty `{memories}` renders an empty section — harmless.

### 3. View (companion.py)

- Pass `user_id=request.user.id` to `generate_response`.
- Replace the silent truncation. After appending the two new turns:
  ```python
  if len(history) > 5:
      evicted = history[:-5]
      companion_service.remember(request.user.id, evicted)
      history = history[-5:]
  ```
  (i.e. the turns that fall out of the window are handed to long-term memory before being dropped.)

### 4. DI

`companion_service` provider gains `memory_service=agentic.memory_service`.

## Data flow

```
POST /companion/interact
  ├─ retrieve: memory_service.retrieve_relevant_memories(user_id, user_msg) ──▶ {memories} in prompt
  ├─ generate response (LLM)
  ├─ append (user, assistant) to session history
  └─ if >5 turns: remember(user_id, evicted)  ──[background thread]──▶ store_memory → pgvector
                  history = history[-5:]
```

## Error handling

- Retrieval is guarded inside `retrieve_relevant_memories` (returns "" on failure) — the companion
  degrades to no-memory, never errors.
- Persistence runs in a daemon thread; `store_memory` swallows its own exceptions. A memory failure
  never affects the user's response.
- No `user_id` (anonymous) or no `memory_service` → both retrieve and remember are no-ops.

## Testing (TDD)

- **CompanionService unit:** with a fake `memory_service`, `generate_response(..., user_id="u1")`
  passes the retrieved string as the `memories` kwarg to `get_prompt`; with no `user_id` or no
  `memory_service`, `memories` is `""`. `remember("u1", turns)` invokes
  `memory_service.store_memory("u1", turns)` (patch `threading.Thread` to run synchronously so the
  assertion is deterministic); `remember` with no turns / no user / no service is a no-op. Existing
  sanitization + mentor tests stay green (the extra `memories` kwarg doesn't break their
  per-key assertions).
- **View:** posting a turn that pushes history past 5 calls `companion_service.remember` with the
  evicted turn and truncates to 5 (DRF stack with the container's services mocked/stubbed).
- All tests mock the LLM / vector store / threading — CI-safe.

## Risks / mitigations

- **Risk:** the new `{memories}` placeholder breaks real prompt rendering if `get_prompt` isn't
  given `memories`. *Mitigation:* `generate_response` always passes `memories` (defaulting to "");
  the 3 templates are updated together with the call.
- **Risk:** a per-turn summarization cost once past 5 turns. *Mitigation:* accepted — it runs in the
  background; a future batching/episodic-compressor pass can reduce it (follow-up).

## Out of scope / follow-up

- Wire `episodic_memory_compressor` + Neo4j profile linking.
- Batch/throttle summarization to reduce LLM calls on long conversations.
