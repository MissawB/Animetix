# Animetix - History of Refactorings & Achievements

This document archives the major milestones of the project's technical evolution.

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

## [2026-06-01] Session: SOTA Refactoring, Caching, and XState Purge

- **Zustand Migration**: Completely removed XState and `@xstate/react`, refactoring Akinetix and Paradox timelines into lightweight Zustand stores.
- **Anti-DoS Caching Middleware**: Implemented a 15-minute Cache-Control decorator on user personalization computation calls.
- **Cleanup of Unused Packages**: Purged `umap-learn`, `three` (duplicate), and `duckduckgo_search` (replaced by Tavily and Google Grounding).

---
*End of History Log*
