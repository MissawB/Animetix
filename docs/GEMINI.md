# Gemini Project Instructions - Double Scenario Project

This file contains foundational mandates for Gemini CLI interventions in this workspace. These instructions take absolute precedence over general defaults.

## Architectural Mandate: Atomic & Hexagonal Architecture (Ports and Adapters)
The project MUST follow Hexagonal Architecture principles to ensure decoupling between core logic and infrastructure. The architecture MUST be atomic: components should be small, single-purpose, and easily swappable.

### Refactoring Priorities (High Priority)
- **Modularization of UI Logic:** `base.html` has been partially cleaned by extracting JS into `animetix_core.js`. Continue to modularize complex templates (like `animinator.html` or `online_room.html`) and move inline scripts to dedicated static files.
- **Decoupling of Utils:** Global utility functions in `src/backend/animetix/utils.py` (e.g., session helpers) MUST be moved to dedicated ports/adapters or domain services to improve reusability and testability.
- **Error Handling Strengthening:** Systematically replace `except: pass` blocks in IA services (especially in `AgenticRAGService`) with explicit exception handling and structured logging.
- **Prompt Externalization:** Following the `ReasoningAgentService` refactor, ensure ALL other services use `PromptManager` and external YAML files. NO hardcoded prompts in Python files.

- **Domain (Core):** Pure business logic, entities, and use cases.
    - **Entities:** Located in `src/core/domain/entities/`. Use `Pydantic` or `Dataclasses` for structured data (see `ai_schemas.py`).
    - **Services:** Located in `src/core/domain/services/`. MUST use the standard `logging` module (no `print`).
- **Ports (Interfaces):** Located in `src/core/ports/`. Abstract definitions of required external capabilities.
- **Adapters (Infrastructure):** Located in `src/adapters/`. Concrete implementations of ports.
    - **Persistence:** Use `UnifiedRepositoryAdapter` as the primary entry point for media data. It handles both PgVector and ChromaDB fallback.
    - **Inference:** Use `FallbackInferenceAdapter` for LLM resilience. Supports real-time SSE streaming via `stream_generate`.
- **Backend (Driving):** Django application in `src/backend/`. Use `Django Forms` for all user input validation. No raw business logic in views.

## Coding Standards
- **Language:** Python 3.10+
- **Typing:** Mandatory strict type annotations. Return `Pydantic` models for complex AI structures to ensure schema validation.
- **Logging:** Use named loggers (e.g., `animetix.rag`). Standardize on `info`, `warning`, `error`.
- **Prompts:** NEVER hardcode prompts in services. Use the `PromptManager` and external YAML files in `src/core/domain/services/prompts/`.
- **Security:** Sanitize AI outputs using the `sanitize_ai` Django filter (powered by `bleach`).

## Workspace Specifics
- **Pipeline:** Strictly follow Dagster patterns. Neo4j synchronization MUST be automated within asset materialization.
- **Observability:** 
    - **Tracking:** Track LLM token usage and costs using `AITokenUsage` and `UsagePort`.
    - **Metrics:** Use `Ragas` for systematic RAG evaluation (Faithfulness, Relevance).
- **Model Selection:** ALWAYS perform a search (e.g., using `huggingface-best` or `paper_search`) to identify and use the most recent and best-performing models (SOTA) when choosing or updating LLMs, Embeddings, or Vision models.
- **Scalability:** Implement database-side pagination (`limit`/`offset`) in all repository adapters. Use HNSW indexes for vector columns.

## Intervention Workflow
1. **Research:** Map changes to Domain, Port, or Adapter layers.
2. **Strategy:** Explain how the change preserves Hexagonal integrity and strict typing.
3. **Execution:** Implement surgical updates. Add tests in `tests/`.
4. **Validation:** Run `pytest`. Verify architectural boundaries are not breached.
