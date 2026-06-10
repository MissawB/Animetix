# 🎭 Animetix: Complete Technical & Functional Reference Guide

This document serves as the comprehensive technical specification and operations manual for the **Animetix** platform (Anime Archetype Engine). It is designed for AI engineers, fullstack developers, and system architects maintaining or extending this cognitive ecosystem.

---

## 🏛️ 1. Cognitive Architecture: Hexagon 2.0

Animetix is built around an **Atomic & Hexagonal Architecture** (Ports & Adapters), separating pure business workflows from underlying frameworks.

### A. Core Domain (Pure Intelligence)
The domain layer (`backend/core/domain/`) encapsulates the application's core intelligence:
- **Services (e.g., `AgenticRAGService`):** Orchestrate multi-step cognitive agents.
- **InferencePort:** Interface boundary supporting Server-Sent Events (SSE) streaming, Test-Time Compute (TTC) routing, and `rerank_documents` Cross-Encoder operations.
- **PersistencePort (UnifiedRepository):** Defines unified data read/write rules, delegating to vector search indices and Neo4j relational structures.

### B. Infrastructure (Adapters)
- **Persistence:** Concrete adapters implementing database interfaces (Vertex AI, pgvector, Neo4j, Django DB).
- **Inference:** Implementations for cloud services (Google GenAI, BrainAPI) and local endpoints (Ollama, local Transformers). Uses lazy imports to prevent overhead at startup.

---

## 🧠 2. Deep Dive: AI Pipelines & Models

### A. Inference & Reasoning Cascade (LLM & SLM)
Animetix employs a cascade of models to optimize the **Cost / Latency / Accuracy** ratio:
1.  **Thinking Model (8B+ - e.g., DeepSeek-R1 Distill):** Triggered only when the Complexity Analyzer detects highly ambiguous queries. It generates internal logical thought steps (`<thought>`) before outputting text.
2.  **Synthesis Model (8B - e.g., Llama-3 / Qwen-3):** The standard model for high-quality conversational output.
3.  **Scout & Critic (1B-3B - e.g., Phi-4-mini / SmolLM3):** Ultra-lightweight models running on CPU/entry-level GPU for structural sub-second tasks (entity extraction, safety audits, rating).
4.  **BitNet Quantization (1.58-bit):** Employs ternary weights to run models with up to 70% VRAM savings.

### B. Matryoshka Representation Learning (MRL)
Animetix implements MRL on top of the **Jina-v3** embedding model:
- **Concept:** Embedding vectors are trained to pack the most critical semantic information into the early dimensions.
- **Query Flow:**
    1.  **Short-List Phase:** Vector similarity search is executed on the first **128 dimensions** (using an HNSW index). This is up to 8x faster than loading the entire vector.
    2.  **Zoom Phase:** The top 50 matches are re-evaluated using the full **1024 dimensions** for precise ranking.
- **Result:** Semantic search latency is kept below `50ms` on large catalogs.

### C. Multimodal & Audio Pipelines
1.  **Vision Encoder (SigLIP-SO400M):** SigLIP aligns image-text features using a sigmoid loss function, enabling finer image description parsing than traditional CLIP.
2.  **Visual Reranker (Qwen-VL):** For complex visual queries, a Vision-Language Model inspects image files directly to confirm similarity.
3.  **Voice Cloning (RVC):** The `VoiceCloningService` clones character voices from a 10-second reference audio sample (zero-shot) for voice synthesizer playback.
4.  **Gemini Multimodal Live API:** Relays PCM audio bidirectionally over WebSockets, bypassing text transcription for low-latency voice-to-voice companion dialogues.

---

## 🕸️ 3. Knowledge Graph & GraphRAG

### A. Neo4j Ontology
The graph database maps structural relationships:
- **Nodes:** `Media`, `Studio`, `Creator`, `Character`, `MicroTag` (granular themes).
- **Edges:** `PRODUCED_BY`, `CREATED_BY`, `FEATURES`, `HAS_THEME`, `INFLUENCED_BY`.

### B. Graph Algorithms
- **Multi-Hop Traversal:** The agent can navigate relationships (e.g., *"Find anime produced by the studio that made 'Arcane' but with an art style resembling 'Spirited Away'"*) by traversing graph nodes before performing vector similarity matches.
- **Leiden Community Summarization:** Runs community detection (Leiden algorithm) on Neo4j to summarize global knowledge clusters (e.g., "History of Cyberpunk in the 90s").

---

## 🎮 4. Game Modes In-Depth

### 1. Paradox Quest (Neuro-Symbolic Logic)
*   **Engine:** Fuses LLMs with a formal logic solver (Z3).
*   **Workflow:**
    1.  **Fact Extraction:** The LLM extracts narrative properties of titles as Boolean states.
    2.  **SAT Solver:** The **Z3 Solver** processes these predicates to mathematically prove which item is the intruder.
    3.  **Narrative Rendering:** The LLM translates the logical contradiction into a riddle.

### 2. Akinetix RL (Reinforcement Learning)
*   **Engine:** Proximal Policy Optimization (PPO).
*   **Workflow:** The agent has been trained in a simulated Gym environment (`AkinetixRLService`) to select questions that maximize information gain (entropy), guessing the player's character in minimal turns.

### 3. La Forge (Multimedia Generation)
*   **Engine:** Stable Diffusion XL + IP-Adapter + ControlNet.
*   **Workflow:** Fuses two creative IPs. The LLM generates a hybrid synopsis, while the diffusion pipeline generates posters preserving character features and postures.

### 4. Spatial Computing (3D Reconstruction)
*   **Engine:** DepthAnything + Three.js renderer.
*   **Workflow:** Estimates depth maps from 2D posters and generates a 3D volumetric scene, rendering a navigable diorama in the browser.

---

## 📊 5. MLOps, Security & Observability

### A. Real-Time Critic (Ragas)
Animetix employs an **LLM-as-a-Judge** evaluation loop:
- Every generation is audited on Ragas metrics (Faithfulness, Relevancy).
- If Faithfulness falls below `0.7`, a safety disclaimer is attached, or the response is rewritten.

### B. DPO Pipeline (Direct Preference Optimization)
- **Ingestion:** User upvotes/downvotes and corrections are captured.
- **Feedback Loop:** Malformed generations are formatted into `(Prompt, Chosen, Rejected)` JSONL datasets.
- **Alignment:** Datasets are used for continuous LoRA training.

---

## 🛡️ 6. Safety & Compliance

- **SQL Guardrail:** Natural language text-to-SQL inputs are audited via `sql_guard.py` to prevent SQL injection, multi-statement queries, comments, or unauthorized table access.
- **Prompt Sanitization:** Ingested context is audited to block indirect prompt injections.
- **Rate Limiting:** Protects models from Token DoS attacks.
- **OpenTelemetry Tracing:** Spans are enriched with semantic agentic attributes and exported directly to Cloud Trace.

---

## 🚀 7. Deployment Lifecycle

1.  **Staging:** Deploy using Docker Stack (Postgres, Redis, Neo4j, Ollama).
2.  **Pre-Flight:** Execute `scripts/pre_flight_check.py` to validate environment bindings.
3.  **Production:** Enable Daphne ASGI server for SSE streaming and WebSockets.

---
*End of Technical Document - Animetix - June 2026*
