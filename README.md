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

## Architecture & Tech Stack

Animetix strictly follows **Hexagonal Architecture** (Ports & Adapters) to ensure business logic remains independent of infrastructure.

### Core Technology
- **Backend:** **Django 5.0** + **Channels** (WebSockets) for real-time interactions.
- **Orchestration:** **Dagster** manages the entire ETL & ML pipeline.
- **Vector DB:** **ChromaDB** with HNSW indexing for lightning-fast similarity search.
- **Graph DB:** **Neo4j** for modeling complex relationships and attributes.
- **Inference:** Local LLMs served via **FastAPI** with **BGE-Reranker** for precision.

### MLOps Loop
- **RLHF Pipeline:** Collects user feedback (`AIFeedback`) to continuously align model performance.
- **Data Intelligence:** Automated ingestion from AniList, Jikan, and TMDB.
- **Tracking:** Experiment monitoring via **trackio**.

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
python src/backend/manage.py migrate
python src/backend/seed_achievements.py
python src/backend/manage.py sync_catalog
python src/backend/manage.py runserver
```

---

## 📂 Project Structure

```text
Double_scenario_Project/
├── src/                    # Source Code
│   ├── core/               # Domain Layer (Pure Logic, Entities, Ports)
│   ├── adapters/           # Driven Adapters (DB clients, APIs)
│   ├── backend/            # Driving Adapter (Django Web App)
│   └── pipeline/           # Data Ops (Dagster Assets & Ops)
├── scripts/                # Maintenance, Utility & Sync scripts
├── data/                   # Persistent Data Store
│   ├── chroma_db/          # Vector Store
│   ├── artifacts/          # Processed JSON metadata
│   └── models/             # Local LLM weights & adapters
├── deploy/                 # Deployment & Containerization
├── docs/                   # Documentation & Architecture
└── tests/                  # Test Suite (Pytest)
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

