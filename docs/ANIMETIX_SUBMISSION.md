# 🎭 Animetix: Next-Gen Media Discovery & AI Games

This document compiles the comprehensive details of **Animetix** (Anime Archetype Engine) formatted for project presentations, submissions, or portfolios.

---

## 💡 Inspiration

Traditional media discovery is fundamentally broken. Standard platforms rely on rigid keyword searches, collaborative filtering, or basic category tags that fail to capture the deep, thematic, emotional, and visual nuances of rich narrative media like Anime, Manga, and Games. A user looking for a *"90s cyberpunk story dealing with existential dread and synthetic human memories"* is often met with generic recommendation lists simply because they contain the tag "Sci-Fi".

We built **Animetix** to solve this. Our inspiration was to construct a cognitive engine that doesn't just match keywords, but truly *understands* stories, visual aesthetics, soundscapes, character archetypes, and creator relationships. We envisioned a platform that bridges two worlds:
1. **Semantic Knowledge Discovery:** Unifying vector databases (intuitive memory) and knowledge graphs (logical relationships) into a cohesive RAG 2.0 system.
2. **Generative Gaming Playground:** Moving away from standard, boring conversational chat-bots to engineer a highly interactive, real-time suite of AI-driven games that push the absolute boundaries of reinforcement learning, neuro-symbolic reasoning, and multimodal generation.

---

## 🕹️ What it does

Animetix is an intelligent ecosystem composed of two primary engines: a **Cognitive Discovery Engine** and an **AI-Driven Game Suite**.

### 1. Intelligent RAG 2.0 Discovery
* **Hybrid Cognitive Memory:** Integrates **ChromaDB** for vector semantic indexing (HNSW search over plot outlines and tropes) and **Neo4j** for complex relationship traversals (interconnecting studios, creators, characters, and adaptations.)
* **Multi-Scale Search (MRL):** Employs **Matryoshka Representation Learning** (using Jina-v3) to run lightning-fast rough filters on the first 128 dimensions, then zooming into the full 1024-dimensional space for exact matches.
* **Cross-Encoder Reranking:** Leverages a **BGE-Reranker** to analyze query-context pairs jointly, calculating an absolute relevance score to ensure high precision and combat hallucination.

### 2. The AI-Driven Game Suite
* **Akinetix (The Guesser):** An AI game inspired by Akinator. Powered by an agent trained via **Proximal Policy Optimization (PPO)** in a simulated game environment, the model dynamically calculates the mathematical entropy of its knowledge base to ask the most highly-discriminant questions, guessing your character in record time.
* **The Paradox (Neuro-Symbolic Logic):** A game of pure deduction. The AI extracts thematic properties of various works (Neural LLM) and feeds them into a formal logic solver (**Z3 Solver**). The system mathematically proves which title violates the logical rules (SAT Proof) and translates this cold proof into an accessible, narrative riddle.
* **La Forge (Creative Fusion):** A multimedia workshop allowing users to merge styles. Using **Stable Diffusion XL (SDXL)**, **IP-Adapter**, and **ControlNet**, it can take a franchise character and redraw them in the distinct visual style of Studio Ghibli or Akira Toriyama. It also uses **XTTS-v2** to clone the voice of the characters for zero-shot text-to-speech interaction.
* **Vision Quest:** A multimodal quiz challenging players to identify classic visual tropes, animation techniques, and key frames using advanced Vision-Language Models (VLM).
* **Animinator (The Oracle):** An interactive question-answering agent that uses reasoning steps (`<thought>` tags via Test-Time Compute) and is evaluated by a real-time **Response Critic** and **Response Judge** to prevent factual errors.
* **Emoji Decode:** A translation challenge where complex synopses are translated into highly compressed emoji sequences for players to decode.

---

## 🏗️ How we built it

We designed Animetix from the ground up to follow **software engineering best practices**, making it modular, scalable, and highly maintainable:

* **Atomic & Hexagonal Architecture:** Decoupled our core business rules (Domain Services, Game Engines, and DTOs) from infrastructure adapters (Persistence, AI Models, and APIs) using strict **Ports and Adapters** interfaces.
* **Decoupled Pure SPA Frontend:** Built a modern, blazing-fast web application using **React + Vite** and `react-router-dom` on the client side, communicating asynchronously with the backend via REST endpoints and real-time WebSockets (Django Channels).
* **Headless Django API:** Refactored Django to act purely as a headless backend API, purging all legacy HTML templates, view controllers, and static assets in favor of a clean, stateless JSON API.
* **Unified Inference Engine & Fallbacks:** Designed a `FallbackInferenceAdapter` that orchestrates a latency-aware, error-tracking chain of adapters supporting cloud inference (**BrainAPI**) and local models (**Ollama**, Hugging Face **Transformers**, and **Diffusers**).
* **Robust MLOps Pipelines:** Built automated data ETL and ingestion pipelines. These pipelines orchestrate scrapers for Jikan (MyAnimeList), AnimeThemes (musical data), IGDB (video game adaptations), and Gemini (extracting narrative tropes and TV Tropes clichés).
* **Cognitive Swarm Paxos:** Designed a `SwarmConsensusOrchestrator` that queries multiple specialized agent experts (Visual, Acoustic, and Lore Experts) and achieves consensus on facts through a single-call LLM query optimized via dynamic Pydantic structures.

---

## ⚡ Challenges we ran into

Building a high-performance, local-first AI system came with severe technical bottlenecks:

1. **GPU/CPU Resource & Memory Guard (OOMs):** Loading massive neural weights for SDXL, XTTS v2, and video processing models on consumer setups often resulted in Out-of-Memory crashes. We engineered a **CUDA Dynamic GPU Check** inside our inference adapters. If a CUDA-enabled GPU is missing, the backend automatically intercepts the error and routes the heavy text/audio request to our remote cloud provider (**BrainAPIAdapter**) while locally falling back on a Pillow-only, CPU-safe engine for image manipulation and manga translation.
2. **Systematic Network Isolation in Tests:** Ensuring that our unit and integration tests are 100% offline and hermetic without hitting real Jikan or MyAnimeList endpoints. We migrated the entire test suite mocks from standard `requests` to asynchronous `httpx` adapters, isolating network traffic entirely.
3. **The Namespace Import Conflict:** Transitioning Python directories and restructuring the codebase caused massive import path collisions between test targets and runtime environments. We solved this by developing the **Universal Test Mock Injection Mapper (`AliasLoader`)** using a dynamic `sys.meta_path` hook inside `conftest.py` to seamlessly rewrite import bindings at runtime.
4. **Transition to a Pure SPA:** Purging all legacy coupled Django views and consolidating the application state into pure client-side routes required a major rewrite of standard routing mechanisms, resulting in a robust, uniform fallback view matching all SPA endpoints.

---

## 🏆 Accomplishments that we're proud of

* **RAG 2.0 Cohesion:** Bridging the gap between the search speed of vector stores (**ChromaDB**) and the deep relationship reasoning of graphs (**Neo4j**) to prevent context fragmentation.
* **Perfect Test Suite Stability:** Restoring and passing a massive test suite of **over 430 tests** with full mock coverage, ensuring all services are production-ready.
* **The Z3 Solver Fusion:** Fusing creative LLM outputs with absolute mathematical logic solving to create a perfectly balanced, provable deductive game (**The Paradox**).
* **Defensive AI Engineering:** Implementation of strict evaluation guardrails (**ResponseCritic**, **ResponseJudge**), Paxos-style Swarm consensus, and a failsafe RAG mode that ensures high factuality scores and guarantees user safety.

---

## 📚 What we learned

* **The Beauty of Clean Architecture:** Separating systems via Hexagonal Ports saved us hundreds of hours. When we replaced or modified inference models (like switching between GGUF, Ollama, and Cloud APIs), the core game logic of Akinetix and Paradox remained completely untouched.
* **Lazy Imports are Mandatory:** Importing PyTorch, Diffusers, and Transformers synchronously at startup adds massive overhead. By designing an attribute-based `lazy_import.py` wrapper, we reduced app startup times from seconds to less than **50ms**.
* **Reinforcement Learning vs. Static Rules:** Transitioning Akinetix from hardcoded heuristic rules to a dynamic PPO agent trained inside a gym environment showed us how powerful RL can be for creating natural, intelligent, and highly challenging game dynamics.

---

## 🚀 What's next for Animetix

Our cognitive roadmap stretches far into advanced MLOps, deep reasoning, and quantum user modeling:

* **ColBERT Token Search (Phase A):** Implementing the `LateInteractionColBERTAdapter` to search for extremely specific, granular narrative details rather than whole-sentence meanings.
* **Hierarchical GraphRAG (Phase A):** Running community detection (Leiden algorithm) on Neo4j to summarize global knowledge clusters for high-level, open-ended user questions.
* **Tree of Thoughts (Phase E):** Integrating **Monte Carlo Tree Search (MCTS)** for complex queries where the AI can self-evaluate multiple alternate reasoning paths before rendering responses.
* **Neuro-Symbolic Profiling (Phase F):** Storing user preferences as logical predicates in **Z3** to automatically apply mathematically consistent filters on searches.
* **Quantum Cognitive Modeling (Phase I):** Applying quantum state probability vectors (Born's rule) to represent the shifting state of user choices and preference orders during interactive sessions.

---

## 🛠️ Technology Stack & Detailed Dependencies

The platform leverages a cutting-edge stack spanning front-end rendering engines, hybrid databases, heavy local & cloud machine learning frameworks, and robust software engineering architectures.

### 1. Languages
* **Python (3.11+)**: Powers the backend domains, pipeline assets, agent consensus logic, and heavy AI model runtimes.
* **TypeScript & JavaScript (ES6+)**: Powers the React client application and Playwright end-to-end integration tests.
* **SQL & Cypher**: Used for complex schema transactions (SQLite/PostgreSQL) and topological relational queries (Neo4j), respectively.

### 2. Backend Architecture & Web Frameworks
* **Django (5.2)**: Core web framework acting strictly as a headless backend API server.
* **Django REST Framework (DRF)**: Powers the modular rest-endpoints, schema generators, and input validators.
* **Django Channels & Daphne**: ASGI middleware and webserver delivering real-time bi-directional game events over WebSockets.
* **FastAPI & Starlette**: Used for asynchronous background endpoints.
* **Dependency-Injector (4.49)**: Handles declarative Dependency Injection to decouple Ports from Adapters.
* **Celery & Redis**: Background job distribution for user metrics, DPO feedback tracking, and heavy telemetry logs.

### 3. Frontend Architecture & Rich Visualization
* **React (19)**: Virtual DOM UI system rendering a responsive Single Page Application.
* **Vite (8)**: Super-fast HMR frontend bundler.
* **Tailwind CSS (3.4) & Autoprefixer**: Flexible utility-first styling for fluid layouts.
* **Framer Motion (12)**: Fluid CSS transitions and subtle micro-animations for high-fidelity gaming components.
* **Zustand (5) & XState (5)**: Client state containers and finite-state machines driving complex, deterministic game timelines.
* **TanStack React Query (5)**: Server-state synchronization, request deduplication, and local key-value caching.
* **React Router DOM (7)**: Client-side URL routing.
* **React Force Graph 2D & d3-force**: Renders an interactive 2D visualization of the Neo4j knowledge graph.
* **Plotly.js & React-Plotly.js**: Interactive chart builders for ML diagnostic uncertainty analysis (per-layer logits, attention entropy).
* **Howler.js**: Powers real-time high-fidelity game audio and dynamic soundscapes.

### 4. Databases, Vector Stores, & Cache
* **ChromaDB (1.5)**: HNSW vector search database acting as semantic memory.
* **Neo4j (6.1)**: Distributed Property Graph database modeling anime-character-studio relations.
* **PostgreSQL & psycopg2-binary**: Robust transaction store (with migration scripts).
* **Redis (7.4)**: Real-time channel layering, cache memory, and WebSocket message broker.

### 5. AI, Deep Learning, & Neuro-Symbolic Computing
* **PyTorch (torch/torchvision)**: Core Deep Learning framework for on-premise execution.
* **Hugging Face Hub & Transformers**: Loads model checkpoints, schedules tokenization, and runs local pipeline tasks.
* **Diffusers (0.37)**: Generative image models (SDXL, IP-Adapter, ControlNet, Img2Img).
* **Ollama (0.6)**: Local serving for LLMs (Llama-3, DeepSeek-R1) and VLMs (Qwen2-VL, Moondream).
* **Coqui-TTS (0.27) & XTTS v2**: High-quality Zero-Shot voice cloning (RVC).
* **Kyutai Moshi (moshi)**: High-performance Speech-to-Speech (S2S) low-latency local execution.
* **MangaOCR (0.1) & TrOCR**: OCR character-segmentation parsing for manga dialogue bubbles.
* **Sentence-Transformers (3.3)**: Generates high-dimension sémantiques embeddings (Matryoshka Jina-v3, CLIP).
* **Ragas (0.4)**: Automated RAG metrics scoring framework (Faithfulness, Relevancy) acting as an LLM-as-a-judge.
* **Z3-Solver (4.16)**: High-performance formal logic theorem prover solving thematic contradictions in Paradox Quest.
* **Instructor (1.15) & Pydantic (2.12)**: Enforces structural Pydantic validation on model responses.
* **LangChain & LangGraph**: Agentic state charts, checkpoint memory, and flow controls.

### 6. External APIs, Scraping & Search Services
* **Jikan API (MyAnimeList wrapper)**: Fundamental anime ratings, studio casting, and recommendations.
* **AnimeThemes API**: Opening and ending soundtracks, composer entries, and media links.
* **IGDB API (Twitch OAuth2)**: Real-time query matching for franchise video game adaptations.
* **DuckDuckGo Search (ddgs)**: Agentic web search engine routing real-time facts into RAG 2.0.
* **Google GenAI / Gemini API**: Offload engine for TV Tropes extraction, synopsis scouting, and Seichijunrei geolocation tagging.
* **BrainAPI**: Primary high-availability cloud inference.

### 7. Observability, Telemetry & Diagnostics
* **Sentry SDK**: Error logging and APM trace reporting.
* **PostHog**: Frontend session replay analytics.
* **Prometheus & django-prometheus**: Metrics collection, uptime health checks.
* **OpenTelemetry**: High-fidelity RAG transaction tracing.

### 8. Testing & Development Pipeline
* **Pytest (Pytest-Django, Pytest-Mock)**: Main backend test framework running 430+ hermetic tests.
* **Playwright (Python & Node.js)**: Orchestrates end-to-end integration and Visual Regression Testing (VRT).
* **Vitest & JSDOM**: Lightweight frontend component unit tests.
* **Storybook (10)**: Dynamic UI component cataloging with built-in accessibility (a11y) auditing.

