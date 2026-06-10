# GEMINI - Animetix Project Mandates

This file defines the absolute rules and technical constraints of the workspace.

> [!IMPORTANT]
> Specific instructions are available for sub-domains:
> - [Backend Mandates](../backend/GEMINI.md)
> - [Frontend Mandates](../frontend/GEMINI.md)

## 🏗️ Hexagonal Architecture (Ports & Adapters)
All modifications must strictly respect the separation of layers:

- **Domain (Core):** `backend/core/domain/`. Pure business logic, without external dependencies.
    - *Entities:* Use `Pydantic` for structure validation (`ai_schemas.py`).
    - *Services:* High-level logic. Do not use `print()`, use the standard `logging` module.
- **Ports (Interfaces):** `backend/core/ports/`. Abstract boundary definitions for external capabilities.
- **Adapters (Infrastructure):** `backend/adapters/`. Concrete infrastructure implementations.
    - *Persistence:* `UnifiedRepositoryAdapter` (Vertex AI Vector Search / pgvector).
    - *Inference:* `FallbackInferenceAdapter` (LLM Resilience + Streaming).
- **Presentation (Driving):** `backend/api/`. Headless Django API. Input validation via `Django Forms` is mandatory for user inputs.

## 📝 Code & AI Standards
- **Typing:** Python 3.10+. Strict type annotations are mandatory on all functions.
- **Logging:** Named loggers (`animetix.rag`). Levels: `info`, `warning`, `error`.
- **Prompts:** ZERO hardcoded prompts. Exclusively use `PromptManager` (YAML files).
- **Security:** Systematically sanitize LLM outputs with the `sanitize_ai` filter.

## 🚀 Workspace & MLOps Specifics
- **Pipeline:** Automated synchronization commands and scheduled tasks (Django management commands). Automated Neo4j synchronization.
- **Observability:** 
    - Systematic tracking of tokens/costs via `UsagePort`.
    - RAG evaluation via `Ragas` (Faithfulness, Relevance).
- **SOTA Search:** Before choosing or updating a model, use the `huggingface-best` skill to identify the current best candidate.
- **Performance:** DB-side pagination (`limit`/`offset`). HNSW index for vector representations.

## 🛠️ Intervention Workflow
1. **Research:** Map changes to Domain, Port, or Adapter layers.
2. **Strategy:** Justify compliance with hexagonal integrity and strict typing.
3. **Execution:** Surgical implementation + add tests in `tests/`.
4. **Validation:** Run `pytest` and verify layer boundaries.
