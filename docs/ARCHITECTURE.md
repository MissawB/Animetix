# Technical & Modular Architecture (Atomic & Hexagonal)

This document describes the software architecture of the **Double_scenario_Project** (Anime Archetype Engine). The project adopts an **Atomic & Hexagonal** (Clean Architecture) approach to guarantee a strict decoupling between the business logic (Domain) and the infrastructure layer (Adapters).

---

## 1. Overview of the Hexagon

The architecture is divided into three distinct layers:

```mermaid
graph TD
    subgraph Frameworks & Adapters (External)
        Django[Django Backend & Channels]
        ML_Adapters[Inference Adapters: LocalLlama, Diffusers, Transformers]
        Persistence_Adapters[Persistence Adapters: Vertex AI, pgvector, Neo4j, Django DB]
    end

    subgraph Ports (Interfaces)
        InferencePort[InferencePort - includes Reranking]
        PersistencePort[PersistencePort - UnifiedRepository]
    end

    subgraph Core Domain (Business Logic)
        Services[Domain Services: AgenticRAGService, PromptManager, Games]
        Models[Pydantic Models: DTOs, AI Schemas]
    end

    Django --> Services
    Services --> InferencePort
    Services --> PersistencePort
    ML_Adapters --> InferencePort
    Persistence_Adapters --> PersistencePort
```

---

## 2. Source Code Structure

The backend code is organized under `backend/`:

- **`core/ports/`**: Abstractions (Abstract Base Classes) defining the business contracts.
  - `InferencePort`: Text/Image generation, voice cloning, reranking, and advanced computer vision.
  - `MlopsPort`: Handles telemetry, DPO logging, and AI feedback loops via Cloud Run Jobs / GCP Tasks.
  - `PersistencePort`: Unified data access definition (`UnifiedRepositoryAdapter`).
- **`core/domain/services/`**: Pure business logic services, completely independent of infrastructure or frameworks.
- **`adapters/`**: Concrete infrastructure implementations.
  - `adapters/persistence/`: Handles data multi-sources (Vertex AI, pgvector, Neo4j, Django DB).
  - `adapters/inference/`: Adapter implementations for Google GenAI, BrainAPI, Ollama (Unified), and local Transformers.
- **`api/`**: Headless Django presentation layer, split by domain (`animetix/api/core/`, `animetix/api/labs/`, `animetix/api/games/`, SSE stream views). Dependencies are declared in `containers/` (Dependency-Injector) and **constructor-injected** into every view (`@inject __init__` with `Provide[...]` defaults) — there is no service-locator access left in the view layer; tests override the container providers.

---

## 3. Storage & Persistence

The project utilizes **PostgreSQL + pgvector** (serverless Neon) in production and **NumPy (SQLite)** as the zero-configuration local fallback for semantic vector searches; a **Vertex AI Vector Search (Collections)** adapter exists as an optional managed alternative. Data access is unified under the `UnifiedRepositoryAdapter`. Additionally, **Neo4j** (Aura in production) acts as the graph database mapping complex, topological creator-studio-character relations.

---

## 4. Lazy Imports Strategy

To optimize startup performance and keep memory usage low, heavy AI libraries (`torch`, `transformers`, etc.) are imported lazily using an attribute-based wrapper (`lazy_import.py`). The actual module import is only triggered during the first attribute access, eliminating unnecessary loading overhead for non-AI tasks.

---

## 4bis. Async / Sync Strategy

The codebase is **synchronous by default**, with `async` deliberately confined to two edges. This is the canonical Django + Channels model — keep it; do **not** "async-ify" the core.

- **Core domain & DRF views are SYNC.** Domain services (`core/domain/services/`) expose synchronous public APIs (e.g. `ReasoningAgentService.solve_complex_query`, the RAG services, game logic). DRF request handling is sync. Inference adapters are sync.
- **Async edge #1 — ASGI / Channels consumers** (`api/animetix/consumers/`): WebSocket consumers are `async` because they run on the ASGI event loop (real-time duel, codemanga, notifications, Gemini Live…). This is the *only* place async is the default.
- **Async edge #2 — Native async SSE stream views** (`api/animetix/api/streams.py`): the five Server-Sent-Events views (Animinator, Emoji, Paradox, Tree-of-Thoughts, Agentic RAG) are plain async Django views (outside DRF) consuming the adapters' native `astream_generate` — the worker thread is freed for the whole duration of a stream. Session/ORM access goes through `sync_to_async`.
- **Async edge #3 — Multi-agent bus subsystem** (`multi_agent_bus`, `orchestrator_agent_service.execute_workflow`, `reasoning_agent_service._on_bus_message`): Redis pub/sub over `asyncio`. Its `async` methods run **only inside an async context** (the bus loop / a consumer). Note: this subsystem is currently *not wired to any HTTP/WS endpoint* (experimental) — its services expose sync entry points (`solve_complex_query`) for normal use, and the async methods are bus-internal.

**Boundary rules (to keep it coherent):**
1. Never call an `async` method directly from sync request code. If a sync view ever needs the bus, wrap with `asgiref.sync.async_to_sync` — do not spin up `asyncio.run()` per request (it breaks the running loop under ASGI). *(Current count of boundary crossings: zero — the edges don't leak into the core.)*
2. Never perform blocking I/O (DB, sync HTTP) directly inside an async consumer; wrap with `asgiref.sync.sync_to_async`.
3. If the multi-agent bus is ever exposed to users, drive it from an **async consumer**, not a sync DRF view.

For SSRF-safe HTTP, both sync (`safe_http_request`) and async (`safe_http_request_async`) helpers exist in `core/utils/security.py`; pick the one matching your context.

---

## 5. Extensibility & Port Implementation

Adapters implement the abstract ports. Any method not implemented by a specific adapter raises an `InferenceNotImplementedError`. Extending the platform follows a strict pattern:
1. Extend the abstract **Port** definition.
2. Implement the concrete logic in the corresponding **Adapter**.
3. Register or bind the new implementation inside the `containers/` package (and add the consuming module to the `container.wire()` list in `apps.py` if it uses `@inject`).

---

## 6. Deployment: Decoupled Single Page Application (SPA)

Animetix is designed and deployed as a fully decoupled **Pure SPA** (Single Page Application).

- **Frontend (Static)**: A modern React application built with **Vite** (`frontend/`). The production bundle (`dist/`) is built for high performance. In development mode, Vite runs on port `5173` and proxies `/api` and `/ws` requests to the Django backend.
- **Backend (Headless API)**: Django operates strictly as a headless API. All legacy HTML templates and view controllers have been completely removed.
- **Unified Client-Side Routing**: Django routes any non-API fallback paths (`re_path(r'^(?!api/|static/|admin/).*$', spa_view)`) directly to the SPA, allowing React Router DOM to manage application routing on the client side.

---

## 7. Inference Adapters Ecosystem (Local-First Priority)

The project implements a resilient `FallbackInferenceAdapter` that prioritizes free local compute to minimize operational costs (maximizing margin).

```mermaid
graph TD
    FallbackAdapter["FallbackInferenceAdapter"]
    
    subgraph Local_Compute [Tier 1: Free (Priority)]
        Ollama["UnifiedInferenceAdapter (Ollama - API)"]
        Transformers["LocalTextAdapter (Transformers - 4bit)"]
    end

    subgraph Managed_Inference [Tier 2: Managed (Fallback)]
        BrainAPI["BrainAPIAdapter (Custom Central API)"]
    end
    
    subgraph External_APIs [Tier 3: Pay-Per-Token (Last Resort)]
        Gemini["GoogleGenAIAdapter (Gemini, google-genai SDK)"]
    end
    
    FallbackAdapter --> Ollama
    FallbackAdapter --> Transformers
    FallbackAdapter --> BrainAPI
    FallbackAdapter --> Gemini
```

---

## 8. Economy & Monetization: The Berrix Model

Animetix operates on a **Rewarded Economy** where all advanced AI features are 100% free for users, financed by their engagement.

### 8.1. Tokens: The Berrix (Bx)
- **Passive Mining**: Users earn +20 Bx every 3 minutes of gameplay (Blindtest, Akinetix, etc.).
- **Active Injection**: Users can watch 30s sponsored videos ("Rewarded Ads") for +250 Bx.
- **No purchases**: Berrix cannot be bought — the Stripe payment stack was removed entirely (2026-07-07). Earned Bx (play + rewarded ads) is the only currency; the `tier` concept (free/pro) only gates the developer API.

### 8.2. Token Consumption & Protection
Business logic services (`InferencePort`, `Forge`) call the atomic `deduct_berrix` function. If the user's `wallet_balance` is insufficient, the API returns an **HTTP 402 Payment Required** error, which the frontend intercepts to redirect the user to the **Power Station**.

---

## 9. VisionTransformersAdapter Mixin Architecture

To maintain high readability and avoid a monolithic file, the `VisionTransformersAdapter` is modularized into **four specialized mixins**:

```mermaid
classDiagram
    class InferencePort {
        <<abstract>>
        +generate()
        +health_check()
    }
    class DepthEstimationMixin {
        +estimate_depth()
        +generate_3d_scene()
    }
    class MangaOcrMixin {
        +process_manga_page()
    }
    class VideoAnalysisMixin {
        +get_video_temporal_embeddings()
        +localize_video_actions()
        +generate_video_description()
    }
    class ClipVisionMixin {
        +get_image_embedding()
        +classify_image()
        +calculate_visual_similarity()
        +visual_rerank()
        +get_multimodal_late_interaction()
    }
    class VisionTransformersAdapter {
        +detect_objects()
        +generate_image_description()
        +health_check()
    }
    
    InferencePort <|-- VisionTransformersAdapter
    DepthEstimationMixin <|-- VisionTransformersAdapter
    MangaOcrMixin <|-- VisionTransformersAdapter
    VideoAnalysisMixin <|-- VisionTransformersAdapter
    ClipVisionMixin <|-- VisionTransformersAdapter
```

---

## 10. Error Hierarchy

All custom application errors derive from `AnimetixBaseError`:

```mermaid
classDiagram
    class AnimetixBaseError {
        +message: str
        +context: dict
    }
    class DomainError
    class InfrastructureError
    class InferenceError
    class InferenceTimeoutError
    class SpatialComputingError
    class MangaProcessingError
    class VideoProcessingError
    class ImageGenerationError
    class AdapterLoadError
    class ContentModerationError
    class KnowledgeGraphQueryError
    
    AnimetixBaseError <|-- InfrastructureError --|> AdapterLoadError
    AnimetixBaseError <|-- InfrastructureError --|> ContentModerationError
    AnimetixBaseError <|-- InfrastructureError --|> KnowledgeGraphQueryError
```

---

## 11. Access & Deployment Environments

### A. Local Development Environment
The frontend and backend run in isolation to support Hot Module Replacement (HMR).

- **Backend (Django)**: 
  - URL: `http://localhost:8000`
  - Command: `python backend/api/manage.py runserver`
- **Frontend (Vite / React)**: 
  - URL: `http://localhost:5173`
  - Command: `cd frontend && npm run dev`
  - *Note*: Vite automatically proxies `/api/*` and `/ws/*` calls to the Django instance.

### B. Dev / Staging Environment (Docker)
Containers package the entire infrastructure stack, serving the pre-built React frontend directly from the Django static server.

- **Standard Docker**:
  - URL: `http://localhost:8000`
  - Command: `docker-compose -f deploy/docker-compose.yml up`
- **Staging Docker** (includes debugging & experimental feature flags):
  - URL: `http://localhost:8080`
  - Command: `docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.staging.yml up`

### C. Production Environment (Google Cloud Run)
Production runs on **Cloud Run** (region `europe-west9`), behind the custom domain **https://animetix.xyz** (proxied by a Cloudflare Worker, since europe-west9 has no native domain mapping).

- **Services**: `animetix-web` (Django ASGI + built SPA) and a scale-to-zero GPU "brain" service for heavy inference, plus 8 scheduled Cloud Run Jobs (catalog sync, drift baselines, MLOps loops).
- **Secrets**: every credential is mounted from **Secret Manager** (`secretKeyRef`) — no secrets ship in images or env files.
- **Pipeline**: deploys are **manual-only** via `gh workflow run ci.yml -f deploy_to_prod=true` (a push never deploys). All deployment parameters live in the declarative [deploy/deployments.yaml](../deploy/deployments.yaml).

### D. Mirror Deployment (Hugging Face Spaces)
A container mirror can be published to **Hugging Face Spaces** (`https://huggingface.co/spaces/MissawB/Animetix`, internal port `7860`) via `deploy_to_hf.yml` / `scripts/deploy/huggingface/hf_deploy.py`.
