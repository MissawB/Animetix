# Double Scenario Project - Refactoring Roadmap

## Phase 1: High Priority Technical Debt (IN PROGRESS)
- [x] Gestion des Erreurs Silencieuses (`except Exception: pass`)
- [x] Injections Expert en Dur (Refactor `RAGWorkflowManager._get_expert_injections`)
- [x] Journalisation DPO Ad-hoc (Move to Celery / MLOps Port)
- [x] Découplage de `utils/session.py` en Port
- [x] Correction du Hack Device (MangaOcr)

## Phase 2: Missing Features - GGUF & Integration (DONE)
- [x] GGUF Multimodal Expansion (Vision CLIP/Llava support)
- [x] Reranking Visuel natif dans vLLM

## Phase 3: Missing Features - Advanced Multimodal Inference (DONE)
- [x] Vidéo & 3D (estimate_depth, generate_3d_scene, etc.)
- [x] Audio (clone_voice, generate_soundscape)
- [x] Manga (translate_manga_page, inpaint_text_bubbles)

## Phase 4: Pipeline & SPA (DONE)
- [x] Automatisation Synchronisation Neo4j (Dagster)
- [x] Migration des endpoints d'authentification restants
