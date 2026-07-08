# 🎭 Animetix: Next-Gen AI Sandbox & Interactive Games

[![CI](https://github.com/MissawB/Animetix/actions/workflows/ci.yml/badge.svg)](https://github.com/MissawB/Animetix/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Firebase](https://img.shields.io/badge/Google_Identity_Platform-GCIP-orange.svg)](https://cloud.google.com/identity-platform)
[![Vertex AI](https://img.shields.io/badge/Vertex_AI-Vector_Search_2.0-blue.svg)](https://cloud.google.com/vertex-ai)
[![AlloyDB AI](https://img.shields.io/badge/AlloyDB_AI-Text--to--SQL-lightblue.svg)](https://cloud.google.com/alloydb)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow.svg)](https://huggingface.co/spaces)

**Animetix** is a next-generation AI-powered cognitive sandbox and game platform for Anime, Manga, Movies, and Video Games. Powered by a **RAG 2.0 Knowledge Engine**, Animetix fuses advanced semantic graphs, multimodal reasoning, and deep reinforcement learning to power a vast suite of interactive game modes and research-grade AI laboratories.

Built on an **Atomic & Hexagonal Architecture**, the platform runs with enterprise-grade cloud capabilities on **Google Cloud Platform (GCP)** in production, while maintaining a lightweight, zero-configuration local fallback ecosystem for local development.

---

## 📌 Table of Contents

- [🎮 Next-Gen AI Game Suite](#-next-gen-ai-game-suite)
- [🔍 Universal Search Engine](#-universal-search-engine)
- [🧪 The Ghost Labs (Advanced AI Sandbox)](#-the-ghost-labs-advanced-ai-sandbox)
- [🧠 Core RAG 2.0 & Cognitive Architecture](#-core-rag-2-0--cognitive-architecture)
- [☁️ Enterprise GCP Infrastructure](#%EF%B8%8F-enterprise-gcp-infrastructure)
- [🚀 Getting Started](#-getting-started)
- [📂 Project Structure](#-project-structure)
- [📊 MLOps, Security & Observability](#-mlops-security--observability)
- [🧪 Running Tests](#-running-tests)
- [📜 License](#-license)

---

## 🎮 Next-Gen AI Game Suite

Animetix features a rich variety of AI-driven game modes powered by customized domain services:


| Game Mode                      | AI Engine / Mechanics            | Description                                                                                     |
| :----------------------------- | :------------------------------- | :---------------------------------------------------------------------------------------------- |
| **Classic Game**               | Semantic similarity scores       | Challenge your anime knowledge by searching for titles matching specific thematic descriptions. |
| **Akinetix**                   | Entropy-based decision trees     | Think of a media or character; the AI will ask strategic questions to guess it.                 |
| **Akinetix RL**                | Reinforcement Learning (PPO/DQN) | Play against or train a neural network agent learning optimal query strategies.                 |
| **Animinator (Oracle)**        | CoVe Fact-Checking               | Interrogate the AI Oracle. The agent dynamically audits facts before responding.                |
| **La Forge (Creative Fusion)** | Generative fusion & diffusion    | Merge two universes, art styles, or characters to synthesize hybrid works.                      |
| **Forge VN**                   | Interactive Visual Novel         | Experience dynamic, AI-generated branching stories based on your creative fusions.              |
| **Vs Battle Arena**            | LLM Battle Simulation            | Simulate hypothetical battles between characters with comparative capability analysis.          |
| **Emoji Decode**               | Translation sequence models      | Decipher complex plot summaries translated into emojis by an adversarial LLM.                   |
| **Anime Blindtest**            | Audio recognition                | Name the anime from its opening/ending theme (optionally warped by AI), with bonus points for the artist or track number. |
| **Qui Est-Ce? (Quiz Who)**     | Character deduction duel         | A real-time "Guess Who?" duel: narrow down the hidden character through attribute questions.     |
| **Covertest**                  | Cover recognition                | Identify the manga from its cover art alone, against the clock.                                  |
| **Le Paradoxe**                | Temporal reasoning               | Solve chronology puzzles where multiple anime timelines intertwine.                              |
| **Daily Challenge**            | Deterministic daily seed         | One shared daily target per universe — everyone races the same puzzle, tracked by streaks.       |
| **World Boss Raids**           | Cooperative weekly raid          | A code-named boss spawns each week; the whole community deals damage by guessing the hidden work. Defeating it splits an XP reward across every participant, ranked on a contributor leaderboard. |
| **Duel Arena**                 | Realtime 1v1 (WebSockets)        | Face another player head-to-head in a live anime-culture duel.                                  |
| **Multiplayer Labs**           | WebSockets Matchmaking           | Play **Undercover** (find the intruder) or **CodeManga** (Codenames variation) in real-time.    |
| **Vision Quest**               | VLM Multimodal analysis          | Identify visual tropes, frames, and scenes using multimodal vision queries.                     |

---

## 🔍 Universal Search Engine

A single query box unifies metadata, semantics, and multi-agent reasoning through three complementary modes:

* **Meta-Search:** Hybrid lexical + semantic lookup across the entire catalog (anime, manga, characters, seiyuu), filterable by type and backed by the RAG 2.0 engine.
* **Visual Nexus:** Describe a scene in natural language and retrieve the matching temporal video segments via multimodal embeddings.
* **Expert Nexus:** An agentic RAG pipeline that streams its reasoning live over Server-Sent Events — a Monte Carlo Tree-of-Thoughts of specialized agents (semantic router, judge, synthesizer) that grounds every claim before delivering a synthesized answer.

---

## 🧪 The Ghost Labs (Advanced AI Sandbox)

The **Ghost Labs** are specialized playgrounds for exploring cutting-edge machine learning and cognitive architectures directly in the browser:

### 🎙️ Speech & Audio Labs

* **Voice Lab / Zero-Shot Cloning:** Synthesize voices and clone any voice from a short audio sample.
* **Manga Voice Lab:** Click on speech bubbles in a manga panel to generate matching voice-overs using cloned character voices.
* **Speech-to-Speech Live:** Converse with a real-time, bi-directional AI companion using the **Gemini Multimodal Live API** over raw WebSockets.

### 🖼️ Vision & Manga Translation

* **Manga Lab:** Run panel segmentation, optical character recognition (OCR), and translation pipelines on manga scans.
* **Video Lab (FateZero):** Perform temporal frame analysis, translations, and video style transfer using diffusion networks.

### 📐 Spatial Computing & 3D Labs

* **Spatial Lab:** Estimate depth maps from 2D images and export 3D object meshes.
* **Cinematic Volumetric Reconstruction:** View immersive, interactive 3D volumetric scenes rendered in real-time using `Three.js` and depth sensors.

### 🧠 Cognitive & Neuromorphic Sandbox

* **Tree of Thoughts Visualizer:** Watch the Monte Carlo Tree Search (MCTS) reasoning paths and decision trees of the thinking LLM.
* **Swarm Consensus Arena:** Spawn multiple LLM agents, watch them debate a prompt, and reach a unified semantic consensus.
* **Strategy CFR Solver:** Optimize game strategies using Counterfactual Regret Minimization (CFR) solvers.
* **Liquid Neural Networks:** Experiment with continuous-time dynamical LNN models predicting popularity trajectories.
* **Quantum Fiction Lab:** Interactive storytelling where narrative states exist in quantum-like superpositions.
* **Neuro-Symbolic Profile:** Formalize your player profile using **Z3 Theorem Prover** rules derived from user memories.
* **Self-Evolving Compiler:** Let the LLM self-improve and compile optimized backend routines on-the-fly.

---

## 💎 Rewarded Economy: The Berrix Model

Animetix is **100% free** for all users, financed by a sustainable "attention-to-compute" economy. All advanced AI features (Creative Forge, Visual Novel Generation, Deep Graph Visualizer) are powered by **Berrix** (Bx).

*   **Passive Mining**: Earn Berrix simply by playing our suite of interactive games (+20 Bx / 3 min).
*   **Active Injection**: Watch short sponsored clips in the **Power Station** to instantly recharge your neuronal battery (+250 Bx / clip).
*   **Zero-Paywall Philosophy**: No features are locked behind subscriptions. Only the developer API remains subject to strict quotas.

## 🧠 Core RAG 2.0 & Cognitive Architecture

Animetix separates domain rules from infrastructure concerns using a modular hexagonal approach:

*   **Local-First Inference**: Minimizes latency and costs by prioritizing local SLMs (**Qwen-2.5-1.5B**, **Llama-3-8B**) running on GPU Spot instances before falling back to cloud APIs.
*   **Hybrid Memory**: Merges dense vector databases (for semantic similarity) with **Neo4j** (logical knowledge graphs mapping relationships).
*   **Cross-Encoder Reranking**: Fine-tuned cross-encoders score candidate matches to mitigate hallucination.


---

## ☁️ GCP Infrastructure

For production scale and security, Animetix utilizes managed Google Cloud Platform services:

* **Google Identity Platform (GCIP):** Manages user registration and logins (supporting Firebase Web SDK, custom DRF JWT validation, and OAuth providers: Google, Discord, X, MyAnimeList).
* **Vertex AI Vector Search (Collections):** Managed high-dimensional indexing with serverless auto-embeddings (`text-embedding-005`) and RRF search.
* **Cloud Run Jobs & Cloud Scheduler:** Serverless nightly database synchronizations, replacing standard Celery Beat infrastructure.
* **Cloud KMS (CMEK):** Customer-managed encryption keys for GCS buckets containing generated creative assets.
* **Edge Defense (Cloud Armor):** Preempts token-based DDoS, Web application attacks, and prompt injections via CEL filtering.

---

## 🚀 Getting Started

### 📋 Prerequisites

* Python 3.12+
* Node.js 18+ (for frontend development)
* Docker & Docker Compose
* *Optional:* GCP credentials & Firebase config.

### 🐳 Run with Docker (Development Mode)

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/MissawB/Animetix.git
   cd Animetix
   ```
2. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
3. **Spin up containers:**
   ```bash
   docker-compose -f deploy/docker-compose.yml up --build
   ```

   Access the unified SPA on `http://localhost:8000`.

### 🐍 Manual Development Setup

1. **Backend (Headless Django Server):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   # Contributors who run the test suite also need the dev tooling:
   #   pip install -r requirements-dev.txt

   # Initialize SQLite database and media
   python backend/api/manage.py migrate
   python backend/api/manage.py seed_achievements
   python backend/api/manage.py sync_catalog
   python backend/api/manage.py runserver
   ```
2. **Frontend (React SPA):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   The React Vite server runs on `http://localhost:5173` and proxies calls to the backend on port 8000.

---

## 📂 Project Structure

```text
Animetix/
├── backend/                # Headless Django API & Orchestration
│   ├── core/               # Pure Domain Layer (Entities, Ports, Services)
│   │   ├── domain/         # Business domain logic (Akinetix, Swarm, LNN)
│   │   ├── ports/          # Abstract boundary interfaces (InferencePort)
│   │   └── utils/          # Security utilities (SQL Guardrail)
│   ├── adapters/           # Infrastructure Layer (Driven Adapters)
│   │   ├── persistence/    # Vertex AI, pgvector, and AlloyDB adapters
│   │   └── inference/      # Google GenAI and Ollama adapters
│   └── api/                # Presentation Layer (API Views & WebSockets)
├── frontend/               # React Single Page Application
│   ├── src/
│   │   ├── pages/          # Decoupled Page Components (Games, Labs)
│   │   ├── store/          # Zustand Global Stores
│   │   └── features/       # Functional modules (Auth, Companion, Labs)
│   └── vite.config.ts
├── deploy/                 # Docker Compose, GCP templates & deployment configurations
├── docs/                   # Specification plans and historical architecture docs
└── tests/                  # Pytest Unit, Integration, and E2E (Playwright) suites
```

---

## 📊 MLOps, Security & Observability

* **Prompt Sanitization:** Ingested context is audited to prevent indirect prompt injections.
* **Telemetry & Tracing:** RAG decision steps and agent actions are injected into OpenTelemetry spans, which export directly to Google Cloud Trace when active.
* **DPO Loop:** User preferences and corrections are logged to fine-tune local models.

---

## 🧪 Running Tests

### Unit & Integration Suite

With the virtual environment active:

```bash
pytest
```

### End-to-End User Journeys (Playwright)

To execute frontend tests:

```bash
python scripts/verify/setup_e2e.py
pytest tests/e2e
```

---

## 📜 License

Licensed under the [Apache License 2.0](LICENSE).

---

*Developed with ❤️ by the **Animetix Team** - 2026*
