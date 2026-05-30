# 🎭 Animetix: Next-Gen Media Discovery & AI Games

[![Build Status](https://img.shields.io/badge/Build-Success-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)]()
[![Dagster](https://img.shields.io/badge/Orchestration-Dagster-red.svg)]()
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow.svg)]()

**Animetix** is an intelligent ecosystem for exploring Anime, Manga, Movies, and Games. Powered by a **RAG 2.0 architecture**, it combines semantic search, knowledge graphs, and agentic AI to deliver a unique discovery experience and a suite of innovative game modes.

---

## 📌 Table of Contents
- [✨ Key Features](#-key-features)
- [🏗️ Architecture & Tech Stack](#-architecture--tech-stack)
- [🚀 Getting Started](#-getting-started)
- [📂 Project Structure](#-project-structure)
- [📊 MLOps & Observability](#-mlops--observability)
- [📜 License](#-license)

---

## ✨ Key Features

### 🕹️ AI-Driven Game Modes
*   **Animetix Classic:** Semantic search challenge. Find titles based on thematic similarity scores.
*   **Vision Quest:** Multimodal challenges using VLM (Visual Language Models) to identify scenes and visual tropes.
*   **La Forge:** Advanced "Fusion" mode where AI generates hybrid works and archetypes.
*   **Emoji Decode:** Decipher synopses translated into complex emoji sequences by AI.
*   **Animinator (Oracle):** Interrogate the AI Oracle. Uses agentic reasoning to verify facts before answering.
*   **Akinetix (The Guesser):** The AI asks strategic questions to narrow down the media you're thinking of.
*   **The Paradox:** Logic test. Identify the "intruder" among titles using LLM thematic analysis.

### 🔍 Intelligent Discovery
*   **RAG 2.0 Engine:** Harmonizes **ChromaDB** (semantic memory) and **Neo4j** (logical graph memory).
*   **Multimodal Search:** Explore by plot description, visual "vibes", or complex relations.
*   **Semantic Interpreters:** Explains *why* works are related (e.g., "Shared existential themes").

> [!TIP]
> **RAG 2.0** allows Animetix to not only find data but to reason about it using its internal Knowledge Graph.

---

## 🏗️ Architecture & Tech Stack

Animetix is built on an **Atomic & Hexagonal Architecture** (Ports & Adapters), ensuring the core domain is strictly decoupled from infrastructure concerns.

### Core Technology
- **Backend:** **Django 5.0** + **Channels** (WebSockets) for real-time interactions.
- **Dependency Injection:** Custom lazy-loading **DI Container** (`backend/api/animetix/containers.py`).
- **Orchestration:** **Dagster** manages ETL & ML pipelines.
- **Vector DB:** **ChromaDB** (Primary storage) with HNSW indexing.
- **Graph DB:** **Neo4j** for complex relationship modeling.
- **Inference:** Unified **InferencePort** supporting **BrainAPI** (Cloud) and **Ollama** (Local) with automated **Cross-Encoder Reranking**.

### Key Design Principles
- **Atomic Components:** Small, single-purpose modules.
- **Strict Typing:** Python 3.10+ with Pydantic for data validation.
- **Lazy Loading:** Critical for performance; AI dependencies load only when accessed.
- **Observability:** Metrics via **Ragas** and continuous **DPO alignment**.

---

## 🚀 Getting Started

### 📋 Prerequisites
- Python 3.11+
- Docker & Docker Compose
- *Optional:* API Keys for external services (TMDB, IGDB).

### 🐳 Quick Start (Docker)
1.  **Clone the Repo:**
    ```bash
    git clone https://github.com/MissawB/Animetix.git
    cd Animetix
    ```
2.  **Environment Setup:**
    `cp deploy/.env.example .env`
3.  **Launch:**
    ```bash
    docker-compose -f deploy/docker-compose.yml up --build
    ```
    *Access at `http://localhost:8000`*

### 🐍 Manual Development Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run migrations & seed data
python backend/api/manage.py migrate
python backend/api/manage.py seed_achievements
python backend/api/manage.py sync_catalog
python backend/api/manage.py runserver
```

---

## 📂 Project Structure

```text
Animetix/
├── backend/                # Backend & Core Logic
│   ├── core/               # Domain Layer (Entities, Services, Ports)
│   ├── adapters/           # Infrastructure Layer (Driven Adapters)
│   │   ├── persistence/    # ChromaDB, Neo4j, Django DB Adapters
│   │   └── inference/      # BrainAPI, Ollama, Transformers Adapters
│   ├── api/                # Presentation Layer (Django Headless Server)
│   │   ├── animetix/
│   │   │   ├── views/      # Modularized API Views (Classic, Vision, Forge, etc.)
│   │   │   ├── containers/ # Dependency Injection Modules
│   │   │   └── urls.py
│   │   └── manage.py
│   └── pipeline/           # Orchestration Layer (Dagster assets & ops)
├── frontend/               # React SPA (Client Side)
├── scripts/                # Root Utility scripts
├── data/                   # Persistent storage (Vectors, Artifacts, Models)
├── deploy/                 # Docker & CI/CD configs
├── docs/                   # Architecture & Design Docs
└── tests/                  # Unified Test Suite (Pytest)
```

---

## 📊 MLOps & Observability
- **Continuous Alignment:** User interactions feed back into our DPO training loops.
- **Hub Integration:** Models and datasets are automatically synced with **Hugging Face Hub**.
- **Monitoring:** Integrated health checks and performance monitoring.

---

## 🧪 Tests

### Unitaires & Intégration
```bash
pytest
```

### End-to-End (Playwright)
Pour exécuter les tests E2E, vous devez d'abord installer les navigateurs :
```bash
python scripts/setup_e2e.py
pytest tests/e2e
```

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).

---
*Developed with ❤️ by the **Animetix Team** - 2026*

