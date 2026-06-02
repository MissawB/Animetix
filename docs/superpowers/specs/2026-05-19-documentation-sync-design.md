# Documentation Synchronization Design - 2026-05-19

## Context & Objectives
The Animetix project has evolved into a highly sophisticated SOTA 2026 ecosystem. The current documentation (README.md, ARCHITECTURE.md, FULL_GUIDE.md) contains slightly outdated information regarding the primary database (PgVector is now primary), the backend structure (views are modularized), and several advanced AI services (Neuro-symbolic, Spatial computing).

The objective is to synchronize the documentation with the actual implementation to ensure architectural integrity and accurate developer onboarding.

## 1. README.md Updates
- **Architecture Highlights:** Emphasize PgVector with HNSW as the primary vector store.
- **Project Structure:** Update the folder tree to reflect `backend/api/animetix/views/` and the modularized template structure.
- **Getting Started:** Ensure manual setup instructions include the new service seeding.
- **Feature Set:** Explicitly mention "Agentic RAG" and "Multi-modal Vision".

## 2. ARCHITECTURE.md Updates
- **Persistence Layer:** Detail the `UnifiedRepositoryAdapter` logic (PgVector -> ChromaDB).
- **Core Domain:** Explain the Atomic & Hexagonal principles as applied to the new `Container` pattern.
- **Refactoring Status:** Update "Refactoring Priorities" to reflect the completion of the `views.py` modularization and highlight "Utils Decoupling" and "Error Handling" as current priorities.
- **Inference Engine:** Describe the `FallbackInferenceAdapter` for high availability.

## 3. FULL_GUIDE.md Updates
- **Cognitive Loop:** Detail the `AgenticRAGService` workflow (Plan -> Search -> Synthesize).
- **In-Context Learning:** Explain how `PromptManager` handles few-shot injection.
- **Specialized Services:**
    - **Neuro-Symbolic:** Z3 Solver integration for Paradox Quest.
    - **Vision Quest:** SigLIP and Qwen-VL usage.
    - **Spatial Computing:** Voice cloning and native speech LLM.
- **MLOps Loop:** Detail the DPO feedback loop asset in Dagster.

## 4. Verification Plan
- **Consistency Check:** Cross-reference all technical terms (e.g., "UnifiedRepositoryAdapter", "PromptManager") across all three files.
- **Path Verification:** Ensure all file paths mentioned in docs actually exist in the current directory structure.
- **Style Check:** Maintain the professional, high-signal "SOTA 2026" tone.

## 5. Implementation Steps
1. Update `README.md`.
2. Update `docs/ARCHITECTURE.md`.
3. Update `docs/FULL_GUIDE.md`.
