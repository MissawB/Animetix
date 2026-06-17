# How the Animetix AI Engine Works: End-to-End Guide

Welcome to the comprehensive guide to the **Animetix** (Anime Archetype Engine) Artificial Intelligence ecosystem. This document explains the complete data lifecycle and the inner workings of our AI algorithms, from raw ingestion to real-time multimodal user interactions.

👉 **Nouveau :** Pour une analyse détaillée des fondations académiques et scientifiques qui propulsent ce système, consultez notre [Documentation des Papiers de Recherche (RESEARCH_PAPERS.md)](RESEARCH_PAPERS.md).

---

## 🏛️ Cognitive Cycle Overview

Animetix's intelligence does not rely on a single, static Large Language Model (LLM). Instead, it consists of a dynamic **6-phase cognitive cycle** combining ingestion pipelines, hybrid databases, semantic RAG search, logical reasoning solvers, reinforcement learning agents, and continuous MLOps alignment.

```mermaid
flowchart TD
    subgraph Phase 1: Ingestion & Ingestion
        A1[MAL / Jikan Scrapers] & A2[AnimeThemes Scraper] & A3[Gemini / TV Tropes Synthesizers] --> SyncPipeline{Sync Pipeline / ETL}
    end

    subgraph Phase 2: Multi-Layer Structuring
        SyncPipeline --> B1[(SQLite DB)]
        SyncPipeline --> B2[(JSON Reference Files)]
        SyncPipeline --> B3[(Neo4j Knowledge Graph)]
        SyncPipeline --> B4[(Vector Search DB)]
    end

    subgraph Phase 3: Semantic Retrieval (RAG)
        C1[User Query] --> C2[Matryoshka Embedding]
        C2 --> C3[Vector Similarity + Neo4j Multi-Hop]
        C3 --> C4[BGE Cross-Encoder Reranking]
    end

    subgraph Phase 4: Reasoning Agent
        C4 --> D1[Thinking Model DeepSeek-R1]
        D1 --> D2[Internal Thoughts thought]
        D2 --> D3[Synthesis Model Llama-3]
    end

    subgraph Phase 5: Interactive & Multimodal Playgrounds
        D3 --> E1[Akinetix RL - PPO]
        D3 --> E2[Paradox Quest - Z3 Solver]
        D3 --> E3[La Forge - SDXL & Voice Cloning]
    end

    subgraph Phase 6: MLOps & Continuous Improvement
        E1 & E2 & E3 --> F1[LLM-as-a-Judge Ragas]
        F1 --> F2[DPO User Feedback Loop]
        F2 --> F3[GraphHealer & Auto-Fine-Tuning]
    end
```

---

## 🔌 Phase 1: Ingestion & Specialized Scraping

A state-of-the-art AI is only as good as its training/retrieval knowledge base. Animetix continuously compiles specialized data from several external services:

1.  **Jikan (MyAnimeList API Wrapper):** Fetches foundational metadata, ratings, community recommendations, and detailed casting/voice actor profiles.
2.  **AnimeThemes:** Compiles opening (OP) and ending (ED) theme song titles, artists, and music video links to capture the audio identity of anime.
3.  **IGDB (Twitch API):** Maps franchises to their official video game adaptations across all consoles.
4.  **Specialized LLM Synthesizers (Gemini):** Extracts narrative tropes (clichés cataloged from TV Tropes), official streaming platforms availability in France, and real-life geolocations in Japan that inspired backgrounds (*Seichijunrei*).

### The Ingestion Pipeline
All scrapers are structured as scheduled ETL tasks. If a scraping job fails or encounters API rate-limits, it triggers automatic retry policies to respect third-party quotas without crashing the ingestion system.

---

## 🗄️ Phase 2: Hybrid Storage (Multi-Layer Data Architecture)

Once ingested, the data is persisted across four complementary storage engines to optimize different query profiles:

*   **Relational Base (PostgreSQL / SQLite):** Manages relational integrity for user sessions, accounts, profile variables, and transactional metadata.
*   **JSON Reference Files (`clean_root_animes/mangas.json`):** Versions the cleaned dataset directly in the repository, acting as a reliable, offline baseline for local fallbacks.
*   **Knowledge Graph (Neo4j):** Models topological relationships. Entities (`Media`, `Studio`, `Creator`, `Character`) are nodes connected by directed, typed edges (`PRODUCED_BY`, `FEATURES`, `INFLUENCED_BY`).
*   **Vector Search DB (Vertex AI / pgvector):** Stores high-dimensional mathematical embeddings of plots and tropes to execute sub-second semantic lookups.

---

## 🔍 Phase 3: Semantic Retrieval (RAG - Retrieval Augmented Generation)

When a user submits a query (e.g., *"Find a cyberpunk manga from the 90s about human memories"*), Animetix avoids rigid keyword matching. It feeds the query through a modular RAG pipeline:

### 1. Matryoshka Representation Learning (MRL)
The query is vectorized using the **Jina-v3** embedding model, which is optimized with Matryoshka representation learning:
- A "rough" similarity lookup is executed in less than `10ms` on the first **128 dimensions** of the vector (indexing via HNSW).
- The top 50 candidates are then re-scored using the full **1024-dimensional** vector for maximum accuracy.

### 2. Multi-Hop Graph Traversal
Simultaneously, the query context is matched against Neo4j. If a user references a studio, a director, or a specific franchise character, Neo4j traverses relationships to extract connected creators, studio history, and character details.

### 3. Cross-Encoder Reranking
Candidates retrieved from both the vector index and the knowledge graph are unified and sent to a **BGE-Reranker** model. Unlike bi-encoder embeddings that encode queries and documents independently, the Cross-Encoder processes the query-document pair jointly. It outputs an absolute relevance score, filtering out unrelated documents to prevent LLM hallucinations.

---

## 🧠 Phase 4: Reasoning Agent (LLM & Test-Time Compute)

The compiled context, system instructions, and user query are assembled into a prompt and routed based on complexity:

### Complexity Analyzer & Test-Time Compute (TTC)
A lightweight model analyzes the prompt's ambiguity:
- **Simple Queries:** Routed to a lightweight synthesis model (e.g., Llama 3 8B) for a response under one second.
- **Complex / Ambiguous Queries:** Routed to a deep reasoning model (e.g., DeepSeek-R1 Distill). The model uses *Test-Time Compute*, generating chain-of-thought logical steps wrapped within `<thought>...</thought>` tags, resolving contradictions before formulating the final user-facing text.

---

## 🎮 Phase 5: Interactive Game Suite Engines

Animetix's domain services orchestrate multiple advanced game engines:

### A. Akinetix RL (Reinforcement Learning)
Akinetix attempts to guess the character the user has in mind.
- Powered by a neural agent trained via **Proximal Policy Optimization (PPO)** in a custom OpenAI Gym environment.
- The algorithm calculates the mathematical entropy of its character database at each turn, selecting the question that eliminates the maximum number of candidates and minimizing the steps to victory.

### B. Paradox Quest (Neuro-Symbolic Logic)
The user must identify a thematic "intruder" among three titles.
- **Neural Layer:** An LLM extracts Boolean properties and narrative facts from each title.
- **Symbolic Layer:** These facts are compiled into logic predicates and solved via the **Z3 Theorem Prover** (SAT solver). Z3 mathematically proves which title violates the logical properties and constitutes the intruder.
- The LLM then translates the cold logical proof back into a playful riddle.

### C. La Forge (Creative Multimedia Fusion)
Allows users to merge two media styles (e.g., *Dragon Ball* drawn in the art style of *Studio Ghibli*).
- Uses **Stable Diffusion XL** along with **IP-Adapter** (to maintain character features) and **ControlNet** (to guide posture and frame composition).
- Runs **XTTS-v2** to clone the voice of the characters for interactive zero-shot speech.

---

## 📊 Phase 6: MLOps & Continuous Evaluation Loop

The platform self-evaluates and aligns dynamically in production:

1.  **LLM-as-a-Judge (Ragas):** A critic agent audits responses against Ragas metrics:
    - **Faithfulness:** Is the response strictly backed by the RAG context? (Anti-hallucination guard).
    - **Answer Relevancy:** Does the output directly answer the user's intent?
    If the scores fall below a strict threshold (e.g., 0.7), the response is corrected before delivery.
2.  **DPO Preference Ingestion:** User feedback (upvotes/downvotes) and text corrections are captured. Failures are stored in `(Prompt, Chosen, Rejected)` JSONL datasets.
3.  **Continuous Fine-Tuning:** The DPO datasets trigger periodic LoRA fine-tuning workflows to adapt the local models to Otaku culture nuances.
4.  **Autonomous GraphHealer:** A background service monitors the Neo4j graph to detect isolated nodes, dead edges, or lore contradictions, automatically writing Cypher queries to repair and enrich the knowledge graph.
