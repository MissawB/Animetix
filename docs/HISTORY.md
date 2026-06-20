# Animetix - History of Refactorings & Achievements

This document archives the major milestones of the project's technical evolution.

## [2026-06-20] Session: Offline Manga Reader (PWA)

- **Mode Hors-ligne du Lecteur Manga (PWA)**:
  - Added an `offlineLibrary` IndexedDB layer (`idb-keyval`) that stores downloaded chapter page images as blobs with per-chapter metadata, plus a `useChapterDownload` hook exposing download status/progress.
  - Added a chapter list with a per-chapter download button on the manga detail page, and a `useChapterPages` hook that serves the reader from the local cache (object URLs) when a chapter is downloaded, falling back to the network and showing an "indisponible hors-ligne" state when offline.
  - Configured the service worker SPA `navigateFallback` so reader routes load offline.

## [2026-06-20] Session: Mihon/Suwayomi Integration, React Reader UX, Real-Time Chat, and ML Image Worker

- **Manga Reader UX & Suwayomi (Mihon) Integration**:
  - Implemented the Suwayomi explorer integration, image proxy, and extension manager. Added GraphQL queries/mutations to list, install, update, and uninstall manga source extensions, along with Django REST views/routes and explorer dual tabs.
  - Optimized the Manga Reader React UX with background image preloading (next 3/prev 1 pages), double-page side-by-side view (RTL/LTR), wide-page auto-splitting, and infinite scroll Webtoon mode with synchronized scroll-position states.
- **Real-Time Club Chat**:
  - Integrated dynamic chat channels (WebSockets / Django Channels) inside discovery clubs for community interaction.
- **Self-Hosted AI Image Worker (MLOps)**:
  - Added a self-hosted fallback worker for Stable Diffusion and ComfyUI using our task queue (`enqueue_task`) monitored via the Cluster Health dashboard.
- **LLM Speed Optimizations**:
  - Implemented speculative decoding (EAGLE, Medusa) and KV cache optimization (semantic cache and RadixAttention) to accelerate response times.

## [2026-06-20] Session: Multiverse Lore Exporter (PDF Wiki) & LLM Acceleration Research

- **Exportateur de Lore Multivers** :
  - **Backend PDF Generation** : Added `reportlab` dependency to support native high-quality PDF generation. Implemented `MultiverseExportPDFView` inside `multiverse.py` utilizing the custom `NumberedCanvas` class for dynamic page numbering ("Page X sur Y") and header formatting. The API queries Neo4j for the target synthetic universe, its characters, and its neighborhood graph connections (concepts and relations).
  - **URL Registration** : Added `/api/v1/multiverse/<str:universe_name>/export-pdf/` to `urls/api.py`.
  - **React UI Button** : Integrated an "Exporter PDF" button next to the Nexus explorer within the `UniverseDetailPanel` on the `MultiverseCatalogPage.tsx`.
  - **Testing & Verification** : Added a comprehensive test suite in `test_multiverse_export.py` ensuring successful streaming of `%PDF` content and correct attachment headers. Verified the output using a standalone scratch generation pipeline.
- **LLM Acceleration Research** : Evaluated recent research (2025-2026) on speculative decoding (EAGLE, Medusa, SSD) and KV Cache optimization techniques, documented in the artifacts index.

## [2026-06-19] Session: Digital Assets Shop, HTTP Centralisation, Pydantic V2 Migration, and UI Navigation Convergence

- **Boutique d'Actifs Digitaux (Marketplace)**: Fully implemented the digital assets trading platform. Added the `MarketListing` model with choice-based wallet transaction types (`market_purchase`, `market_sale`), Django migrations, and DRF serializers/viewsets. Integrated atomic transactions for safe balances debit/credit and creator transfer. Developed `ShopPage.tsx` using a premium cyber-emerald styling, and linked it via routing and Sidebar. Wrote comprehensive pytest coverage in `test_market_api.py`.
- **Centralisation HTTP (Frontend)**: Refactored game files (`AkinetixRLPage.tsx`, `DuelLobbyPage.tsx`, and `paradoxStore.ts`) to use the centralized `apiClient` wrapper. This eliminates raw `fetch` calls, ensures automatic Firebase and CSRF token transmission, and standardizes error toast feedback.
- **Dépréciations Pydantic V2**: Migrated the `PersonalizationSchema` model in `social.py` from Pydantic V1 class Config format to Pydantic V2 `ConfigDict` standard, successfully resolving deprecation warnings.
- **Correction de `sync-api.bat`**: Aligned the OpenAPI TypeScript code generation target to `src/types/api.d.ts` and removed the unrecognized `--quiet` argument from spectacular schema export.
- **Navigation, Ghost Labs & UI Convergence**:
  - Exposed sidebar shortcuts for **Nexus Pro** and **Transparence Système**, and created the **Outils Admin & Monitoring** section for staff.
  - Linked previously orphan "Ghost Labs" interfaces: **Seiyuu Discovery**, **Numba Compiler**, **Video RAG**, and **Cove Oracle**.
  - Deployed dedicated pages for **Données Hors-ligne** sync status, **AI Feedback History**, and **Open Data** datasets portal.
  - Built the **Tableau de Bord État du Cluster** displaying real-time metrics for H100 GPUs, Ollama engines, and Neo4j nodes.
  - Implemented the **Catalogue de la Galerie Multivers** enabling grid-view filtering and searching of communities' generated multiverses.

## [2026-06-10] Session: SOTA Google Cloud Integrations (GCIP, Vertex AI Vector Search 2.0, Gemini Agent Platform, AlloyDB AI Text-to-SQL, and Cloud KMS CMEK)

- **Google Identity Platform (GCIP) & Firebase Auth**: Migrated local session and allauth authentication to a managed identity platform. Integrated the Firebase JS Client SDK on the frontend and implemented a custom Django REST Framework `GoogleIdentityAuthentication` backend to verify JWT ID Tokens using cached Google certificates (with local Firebase Emulator support). Added OAuth social sign-in support for **Google**, **Discord**, **X (Twitter)**, and **MyAnimeList**.
- **Vertex AI Vector Search 2.0 (Collections)**: Integrated the managed GCP vector search index wrapper (`VertexAICollectionWrapper`) inside `chroma_client.py`. Implemented auto-embeddings (`text-embedding-005`) and hybrid search leveraging Reciprocal Rank Fusion (RRF). Maintained a dynamic runtime fallback to `PGVectorCollectionWrapper` for local SQLite development.
- **Gemini Enterprise Agent Platform & Agentic RAG**:
  - **Agent Gateway**: Integrated proactive safety gates to validate prompt inputs and LLM outputs against Google Cloud safety policies.
  - **Agent Observability**: Enriched OpenTelemetry spans with detailed GCP-specific agentic semantic attributes within `AgenticRAGService` to trace the agent's decision tree.
- **AlloyDB AI - Tools for Data Agents (Text-to-SQL)**: Implemented natural language catalog queries utilizing AlloyDB's native `alloydb_ai_nl.get_sql` function, with a fallback to local LLM prompt generation. Secured database execution with a custom two-layer validation parser (`sql_guard.py`) restricting queries to `animetix_mediaitem`, blocking mutations, comments, and query chaining.
- **Customer-Managed Encryption Keys (Cloud KMS CMEK)**: Integrated CMEK protection for generated assets uploaded to GCS buckets via the `GS_DEFAULT_KMS_KEY_NAME` setting.
- **Documentation Sync**: Fully updated `README.md` and `TODO.md` to reflect the completed cloud integration milestones and their local fallback behaviors.

## [2026-06-09] Session: XAI Convergence, Validation Unification, InferencePort Completion, and Model Collapse Protection (HITL)

- **XAI Convergence**: Merged `UncertaintyService` into `XaiDiagnosticService`. Eliminated duplicated logprob-based entropy and perplexity calculations, simplifying the dependency graph in `AgenticRAGService`.
- **Validation Unification**: Migrated all critical views (`Login`, `Register`, `Akinetix`, `Archetypist`, `Cognition`) from direct `request.data` dictionary parsing to **Django REST Framework Serializers**, stabilizing input validation and error responses.
- **InferencePort Completion**: Implemented all stubbed methods in production adapters. `BrainAPIAdapter` now supports 100% of the interface (video VLM, 3D depth, reranking), and `GoogleGenAIAdapter` integrates Gemini's native temporal video analysis.
- **Model Collapse Protection (HITL)**: Implemented an "Universal HITL Gate" using the `GoldDatasetEntry` model. All synthetic data (Multiverses, Distillation datasets, and QA pairs) are put in a validation queue awaiting human verification before ingestion.
- **Frontend Build Stabilization**: Fixed remaining TypeScript and ESLint build failures following the modularization process.
- **Dependency Cleanup**: Purged duplicate entries for `three` and `plotly` in `package.json`.
- **Ghost Labs Reactivation**: Re-connected all previously comment-stubbed experimental interfaces (Soundscape, Speech-to-Speech, Voice, Visual Nexus) inside `LabHubPage`.
- **Admin Tools & Cognitive Pages**: Hooked up the MLOps Dashboard, DSPy Optimizer, CoVe Oracle (hallucination reduction), Hierarchical Graph RAG visualizer, Strategy CFR Solver, and the Manga Voice Lab pipeline.

## [2026-06-08] Session: Major Refactoring, Frontend Modularization, and Lab Reactivations

- **Django Forms API Validation**: Refactored view methods in `backend/api/animetix/views/api.py` to systematically use Django Forms, eliminating raw request parsing.
- **InferencePort Stubs**: Removed remaining stubs from `backend/core/ports/inference_port.py`.
- **App.tsx Refactoring & Modularization**: Decoupled the monolithic 21 KB `App.tsx` file into atomic components, moving views to `src/pages/` and utilities to `features/`.
- **SelfEvolvingCompiler Integration**: Replaced compiler stubs with an active proxy compiler dynamically rewriting and optimizing performance critical backend paths.
- **Neural Diagnostics Improvement**: Migrated uncertainty analysis from simulated `gpt2` metrics in `UnifiedInferenceAdapter` to production-grade model logprobs.
- **Lazy Load Optimizations**: Configured `FallbackInferenceAdapter` and `GoogleGenAIAdapter` to load heavy client dependencies only on their first runtime invocation.
- **Social Route Cleanup**: Shifted non-social pages (Pricing, Support, Explore) to their respective feature directories.
- **New Feature Dashboards**: Created the `/pricing/` comparison page, Tree of Thoughts MCTS visualizer, Thought Budget (TTC) monitoring dashboard, Multiverse Gallery catalog, and the零-shot Voice Cloning (RVC) lab.

## [2026-06-04] Session: Advanced Explainability (XAI), Direct VPC Egress, GCP Validation, Vertex Context Caching, and Live API

- **XaiReportViewer Component**: Built the React component displaying prompt intent, confidence metrics, agent traces, source attributions, and token logprobs, supported by Vitest suites.
- **Direct VPC Egress Integration**: Replaced serverless VPC connectors with Direct VPC Egress configurations in `deploy_brain.py` and `deploy_jobs.py`.
- **GCP Validation Suite**: Created `test_gcp_deployment_validation.py` to verify Cloud SQL sockets, GCS read/write lifecycles, Secret Manager values, and Cloud Run Job error pathways.
- **Vertex AI Context Caching**: Implemented automatic context caching in `GoogleGenAIAdapter` for prompts exceeding `GEMINI_CACHE_THRESHOLD`.
- **Cloud Armor WAF Protection**: Added `deploy_security.py` configuring CEL expressions to block SQLi, XSS, RCE, Token DoS, and prompt injections.
- **Gemini Multimodal Live API**: Implemented the `speech_to_speech_live.py` Django Channels consumer for PCM WebSocket streaming and updated the frontend client page.

## [2026-06-03] Session: Vector Database Migration (ChromaDB to pgvector)

- **PostgreSQL pgvector Migration**: Replaced standalone ChromaDB containers with the PostgreSQL native `pgvector` extension for production RAG pipelines.
- **Hybrid SQLite Fallback**: Developed a local fallback adapter storing vectors in standard tables and calculating cosine similarity using NumPy.
- **ChromaDB Client Emulation**: Rewrote `pipeline/chroma_client.py` to maintain client compatibility, avoiding rewrite requirements in data scrapers.

## [2026-06-03] Session: Serverless Tasks (Cloud Run Jobs & Cloud Scheduler)

- **Secret Manager Hardening**: Configured Django settings to pull all external credentials directly from GCP Secret Manager in production.
- **ETL Catalog Sync Automation**: Created the nightly `sync_catalog` Cloud Run Job and triggered it via Cloud Scheduler HTTP POST calls.
- **Database Transaction Optimization**: Wrapped the sync command in atomic transactions, reducing execution time from timeouts to 7 minutes.

## [2026-06-03] Session: Google Cloud Storage & Creative Forge

- **GCS Storage Integration**: Configured `django-storages` with Google Cloud Storage backend for production media.
- **Creative Forge Persistence**: Fixed a bug where creative fusions (Base64 URIs) were not saved, implementing default storage decode and write pipelines.

## [2026-06-02] Session: SOTA Inference, Content Moderation, and Gaming UI

- **Google GenAI Adapter**: Built `GoogleGenAIAdapter` using Pydantic structural generation and real logprobs parsing.
- **Homogeneous Content Moderation**: Integrated a standard sémantique safety filter across all adapters with keyword-based fallbacks.
- **DRF Serializer Audits**: Audited and fixed mass assignment vulnerability vectors in `CreativeFusionSerializer` and IDOR vulnerabilities.
- **Gaming & Profile UI**: Deployed ClubEvent countdown participation, realtime notification badges, VsBattle lobby matchmaking, and latent space user auras.

## [2026-06-16] Session: Universal HITL Gate, SQL Guard Hardening, MLOps Privacy, and Frontend Stabilization

- **Universal HITL Gate (Model Collapse Protection)**: Implemented a centralized `SyntheticValidationService` that executes systematic cross-validation (self-critique, XAI scoring, and guardrails) on all synthetic data before human moderation.
- **SQL Guard Formal Audit & Hardening**: Performed a security audit and fuzzing of the Text-to-SQL validator. Implemented mandatory `LIMIT` clauses, restricted `JOIN` counts (max 5), and strictly enforced AST-level table whitelisting for `animetix_mediaitem`. Verified against 34 attack scenarios.
- **MLOps Privacy & Secret Isolation**: Created a recursive data scrubbing utility to strip API keys, JWTs, and PII from logs and fine-tuning datasets (`DPOFeedbackLoop`).
- **Frontend Core Stabilization**: 
    - Resolved UI flicker and unpredictability by replacing `Math.random()` in render cycles with stable deterministic values or `useMemo`.
    - Fixed critical performance regressions by eliminating synchronous `setState` calls within effects in core components (`ClubChat`, `VNPlayer`).
    - Fixed "used before defined" reference errors in `AkinetixRLPage` and `ExpertNexusPage`.
    - **TypeScript Type Hardening**: Massive refactoring to eliminate `any` in core API clients and pages (`Explore`, `Admin`, `Health`), replaced with strict interfaces.
- **InferencePort & Adapters Completion**: Finalized the `InferencePort` implementation across all production adapters. Added real sprite generation for the Game Engine and replaced similarity placeholders with real embeddings in the Google GenAI adapter.
- **Manga & Video Labs Promotion**: Completed the backend flow for the Manga Reader (OCR & Inpainting) and stabilized the temporal indexing service for Video-RAG.
- **Reasoning & Budget Optimizations**: Integrated local 3B reasoning models for low-latency tasks and implemented a dynamic "Reasoning Budget" based on query complexity.
- **Research Lab Expo**: Deployed a dedicated frontend page to showcase and search through the project's 29 fundamental AI research papers.

## [2026-06-14] Session: Backend Robustness, Frontend Type Hardening, Semantic RAG Caching, and UI Convergence

- **Backend Robustness & Observability**: Eliminated the "silent failure" anti-pattern by replacing all identified `except: pass` blocks with explicit logging (`debug`, `warning`, or `error`) across all adapters (Google GenAI, ImageGen, Rerank, Safety), API views, and MLOps loops. This ensures full traceability of system failures in production.
- **Frontend Type Hardening**: Performed a massive cleanup of the TypeScript codebase, replacing generic `any` types with precise interfaces generated from the OpenAPI schema (`api.d.ts`). Secured game stores (`akinetix`, `blindtest`, `vision`, `paradox`), services (`animinator`, `codemanga`, `audioLab`), and XAI components.
- **Semantic RAG Caching**: Implemented a vector-based caching layer in `DjangoSemanticCacheAdapter` using the project's unified vector store (`PGVector`/`ChromaDB`). Cached LLM responses are now reused for semantically similar queries (0.92 similarity threshold), significantly reducing costs and latency.
- **Natural Language SQL Security**: Hardened the Text-to-SQL pipeline by enforcing a strictly **Read-Only transaction** in `DjangoRepositoryAdapter` for all AI-generated queries, providing a final line of defense against injection even if guardrails are bypassed.
- **React Performance Optimization**: Migrated `SocialHubPage` and `ClubDashboard` to **TanStack Query** (hooks `useSocialDashboard`, `useClub`), resolving technical debt regarding synchronous state updates in effects and improving data fetching reliability.
- **UI Routing & Page Convergence**: Finalized the integration of several "Ghost" pages into the main router, including the **Developer Portal**, **Transparency Hub**, **Manga Reader**, and specialized profiles for **Characters** and **Staff**.
- **Stripe Metered Billing for Expert API**: Fully implemented usage-based monetization for the B2B API. Developers can now subscribe to the **Pro tier** via Stripe Checkout. Consumption (RAG requests) is automatically reported to **Stripe Billing Meters** through the `DjangoUsageAdapter`, enabling precise pay-as-you-go invoicing.
- **Documentation Refactoring**: Purged and archived all completed tasks from `docs/TODO.md` into this log to maintain a focused and actionable project backlog.

---
*End of History Log*
