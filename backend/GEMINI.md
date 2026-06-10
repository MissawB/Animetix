# GEMINI - Backend Mandates

This file defines constraints specific to the backend server and AI domain layers.

## 🏗️ Architecture & Dependency Injection
- **Hexagonal Integrity:** Respect the presentation ➡️ core (domain/ports) ⬅️ adapters flow.
- **Dependency Injection:** Utilize the global container located at `backend/api/animetix/containers.py`. All heavy AI dependencies (models, adapters) must be loaded **lazily** to optimize server boot times.

## 🐍 Python & API Standards
- **Version:** Python 3.11+.
- **Validation:** Systematic use of `Pydantic` (v2) for structural entity mappings and AI exchanges.
- **Django:** Use Django `Forms` to validate API parameters. Views must remain thin and delegate logic execution to backend `Domain Services`.
- **Asynchrony:** Use `Django Channels` to stream real-time flows (SSE/WebSockets). Prefer `contextvars` to track request states across asynchronous loops.

## 🧠 Artificial Intelligence & MLOps
- **Pipeline:** ETL sync pipelines must be mapped to Django management commands and run as scheduled tasks (Cloud Run Jobs).
- **Inference:** Requests must go through `InferencePort`. Maintain active routing and fallbacks to Ollama and BrainAPI.
- **RAG:** Synchronize vector indices (Vertex AI Vector Search / pgvector) and the Neo4j Knowledge Graph.

## 🧪 Testing & Quality
- **Test Suite:** Execute `pytest` ensuring full code coverage over Domain Use Cases.
- **Logging:** Never use `print()`. Systematically route logs via named hierarchical loggers.
