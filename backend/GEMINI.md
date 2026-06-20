# GEMINI - Backend Mandates

This file defines constraints specific to the backend server and AI domain layers.

## 🏗️ Architecture & Dependency Injection
- **Hexagonal Integrity:** Respect the presentation ➡️ core (domain/ports) ⬅️ adapters flow.
- **Dependency Injection:** Utilize the global container located at `backend/api/animetix/containers.py`. All heavy AI dependencies (models, adapters) must be loaded **lazily** to optimize server boot times.

## 🐍 Python & API Standards
- **Version:** Python 3.11+.
- **Validation:** Systematic use of `Pydantic` (v2) for structural entity mappings and AI exchanges.
- **Django:** Use DRF `Serializers` for critical API views and Django `Forms` for legacy/simple parameters. Views must remain thin and delegate logic execution to backend `Domain Services`.
- **Asynchrony:** Use `Django Channels` to stream real-time flows (SSE/WebSockets). Prefer `contextvars` to track request states across asynchronous loops.

## 🧠 Artificial Intelligence & MLOps
- **Pipeline:** ETL sync pipelines must be mapped to Django management commands and run as scheduled tasks (Cloud Run Jobs).
- **Inference:** Requests must go through `InferencePort`. Maintain active routing and fallbacks to Ollama and BrainAPI.
- **XAI & Diagnostics:** Use `XaiDiagnosticService` for uncertainty estimation and neural diagnostics (merged from UncertaintyService).
- **Resilience:** Implement the "Universal HITL Gate" and protection against "Model Collapse" via unified validation.
- **RAG:** Synchronize vector indices (Vertex AI Vector Search / pgvector) and the Neo4j Knowledge Graph.
- **Labs:** Support the reactivated "Ghost Labs" (Manga, Video, Spatial, Audio) via their dedicated service ports.

## 🧪 Testing & Quality
- **Test Suite:** Execute `pytest` ensuring full code coverage over Domain Use Cases.
- **Verification:** You **MUST** run and verify all tests (`pytest`), linting (`ruff check . --fix`), and formatting (`ruff format .`) before committing code.
- **Logging:** Never use `print()`. Systematically route logs via named hierarchical loggers.
