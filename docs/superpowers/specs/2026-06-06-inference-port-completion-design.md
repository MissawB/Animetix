# Design Doc: Complétude de l'InferencePort

**Date:** 2026-06-06  
**Status:** In Review  
**Topic:** Supprimer les stubs restants dans `backend/core/ports/inference_port.py` et standardiser l'interface d'inférence.

## 1. Objectifs
- Éliminer les commentaires `TODO` et les stubs inconsistants dans `InferencePort`.
- Définir un contrat clair : méthodes obligatoires (abstraites) vs méthodes optionnelles (avec erreur explicite).
- Assurer que tous les adaptateurs existants respectent le nouveau contrat minimal.
- Préserver les logiques dérivées (modération, structure) comme fonctionnalités "gratuites" pour tout adaptateur.

## 2. Architecture de l'Interface (`InferencePort`)

### A. Méthodes Abstraites (Obligatoires)
Ces méthodes doivent être implémentées par chaque adaptateur car elles constituent le socle de base d'Animetix :
- `generate(...) -> InferenceResponse`
- `stream_generate(...) -> Iterator[InferenceResponse]`
- `get_text_embedding(text: str) -> List[float]`
- `health_check() -> Dict[str, Any]`

### B. Méthodes Optionnelles (Standardisées)
Ces méthodes lèveront `InferenceNotImplementedError` sans commentaire `TODO`. Les services du domaine doivent gérer cette exception comme un manque de capacité de l'adaptateur actuel.
- Vision : `get_image_embedding`, `classify_image`, `detect_objects`, `generate_image_description`.
- Audio/Vidéo : `get_video_temporal_embeddings`, `localize_video_actions`, `generate_soundscape`, `clone_voice`, `speech_to_speech`.
- Créatif/3D : `generate_image`, `estimate_depth`, `generate_3d_scene`, `transform_image_to_anime`, `transform_video_to_anime`.
- Manga : `process_manga_page`, `translate_manga_page`, `inpaint_text_bubbles`.
- Diagnostic : `get_diagnostics`, `calculate_uncertainty`.
- Rerank : `rerank_documents`, `visual_rerank`.

### C. Méthodes Utilitaires (Implémentées par défaut)
Utilisent les méthodes obligatoires pour fournir une logique commune :
- `generate_structured(...)` : Utilise `generate` + regex JSON parsing.
- `moderate_content(...)` : Utilise `generate_structured`.
- `generate_sprite(...)` : Utilise `generate_image`.

## 3. Mise en conformité des adaptateurs

### LocalTextAdapter
- Implémenter `get_text_embedding` : Utilisation de `SentenceTransformer("all-MiniLM-L6-v2")` avec chargement lazy.

### MoondreamAdapter
- Implémenter `generate` : Utiliser `answer_question` avec un prompt par défaut si non fourni.
- Implémenter `stream_generate` : Simple yield de `generate`.
- Implémenter `get_text_embedding` : Lever `InferenceNotImplementedError` (ou fallback via description textuelle).

## 4. Plan de Validation
- Vérifier que `pytest` ne lève pas d'erreurs d'instanciation de classe abstraite sur les adaptateurs.
- Test unitaire pour `InferencePort` vérifiant que les méthodes optionnelles lèvent bien `InferenceNotImplementedError` sans crash.
- Vérification du chargement lazy des modèles dans `LocalTextAdapter`.
