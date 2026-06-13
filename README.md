# 🎭 Animetix: Next-Gen AI Sandbox & Interactive Games

[![Build Status](https://img.shields.io/badge/Build-Success-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)]()
[![Firebase](https://img.shields.io/badge/Google_Identity_Platform-GCIP-orange.svg)]()
[![Vertex AI](https://img.shields.io/badge/Vertex_AI-Vector_Search_2.0-blue.svg)]()
[![AlloyDB AI](https://img.shields.io/badge/AlloyDB_AI-Text--to--SQL-lightblue.svg)]()
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow.svg)]()

**Animetix** is a next-generation AI-powered cognitive sandbox and game platform for Anime, Manga, Movies, and Video Games. Powered by a **RAG 2.0 Knowledge Engine**, Animetix fuses advanced semantic graphs, multimodal reasoning, and deep reinforcement learning to power a vast suite of interactive game modes and research-grade AI laboratories.

Built on an **Atomic & Hexagonal Architecture**, the platform runs with enterprise-grade cloud capabilities on **Google Cloud Platform (GCP)** in production, while maintaining a lightweight, zero-configuration local fallback ecosystem for local development.

---

## 📌 Table of Contents

- [🎮 Next-Gen AI Game Suite](#-next-gen-ai-game-suite)
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
| **World Boss Raids**           | Cooperative Swarm AI             | Join forces with the community to damage an AI boss by submitting thematic solutions.           |
| **Multiplayer Labs**           | WebSockets Matchmaking           | Play**Undercover** (find the intruder) or **CodeManga** (Codenames variation) in real-time.     |
| **Vision Quest**               | VLM Multimodal analysis          | Identify visual tropes, frames, and scenes using multimodal vision queries.                     |

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
* **AlloyDB AI Tools:** Accelerates text-to-SQL operations on database catalogs via native SQL functions (`alloydb_ai_nl.get_sql`).
* **Cloud Run Jobs & Cloud Scheduler:** Serverless nightly database synchronizations, replacing standard Celery Beat infrastructure.
* **Cloud KMS (CMEK):** Customer-managed encryption keys for GCS buckets containing generated creative assets.
* **Edge Defense (Cloud Armor):** Preempts token-based DDoS, Web application attacks, and prompt injections via CEL filtering.

---

## 🚀 Getting Started

### 📋 Prerequisites

* Python 3.11+
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

* **Two-Layered SQL Guardrail:** Prior to execution, generated SQL queries are checked by `sql_guard.py` to prevent multi-statement injection, comments, mutating actions, or unauthorized table access.
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
python scripts/setup_e2e.py
pytest tests/e2e
```

---

## 📜 License

Licensed under the [MIT License](LICENSE).

---

*Developed with ❤️ by the **Animetix Team** - 2026*
