# Double Scenario Project - Refactoring Roadmap (Round 3)

## Phase 1-5: Infrastructure & Technical Debt (DONE)
- [x] All initial infrastructure and debt tasks completed.

## Phase 6: Adapter Consolidation & Specialized Inference (NEW)
- [x] Integration of `MangaOCRAdapter` in `containers.py`
- [x] Suppression des méthodes redondantes dans `TransformersAdapter` (Video, Audio, Manga, 3D)
- [x] Transfert de la logique `generate_3d_scene` vers un service de domaine ou adaptateur dédié
- [x] Correction de l'ordre de priorité dans `FallbackInferenceAdapter`
- [x] Durcissement du typage Frontend (Suppression sélective des `any`)
- [x] Harmonisation des tests `test_creative_inference.py` avec la nouvelle distribution des tâches
