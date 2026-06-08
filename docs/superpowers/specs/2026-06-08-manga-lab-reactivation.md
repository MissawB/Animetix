# Design Doc: Réactivation du Manga Lab (Ghost Labs)

**Date:** 2026-06-08  
**Status:** Approved  
**Topic:** Décommenter et tester les endpoints backend pour le Manga Lab (Nettoyage & Traduction).

## 1. Objectifs
- Réactiver les fonctionnalités "Ghost" de nettoyage et de traduction de planches de mangas.
- Respecter l'architecture hexagonale en s'appuyant sur l'`InferencePort` et le `MangaFlowService`.
- Exposer ces capacités via des endpoints API distincts (principe de responsabilité unique).

## 2. Architecture & Composants

### A. Vues API (`backend/api/animetix/api/labs.py`)
Nous allons créer deux vues distinctes pour séparer le nettoyage et la traduction.

1. **`MangaCleanLabView`** :
   - Endpoint: `POST /api/v1/manga-lab/clean/`
   - Payload: `multipart/form-data` avec le fichier `image`.
   - Logique: Utilise `container.inference.primary().inpaint_text_bubbles(image_bytes, [])` pour nettoyer la planche.
   - Retour: Image encodée en Base64.

2. **`MangaTranslateLabView`** :
   - Endpoint: `POST /api/v1/manga-lab/translate/`
   - Payload: `multipart/form-data` avec le fichier `image` et potentiellement `target_lang` (défaut: French).
   - Logique: Utilise `container.core.manga_flow_service().translate_manga_page(image_bytes, target_lang)` pour orchestrer l'OCR, la traduction LLM et l'inpainting.
   - Retour: Image encodée en Base64.

### B. Routage (`backend/api/animetix/urls/api.py`)
- Remplacer l'ancienne route commentée `# path('manga-lab/', ...)` par les deux nouvelles routes :
  ```python
  path('manga-lab/clean/', api_views.MangaCleanLabView.as_view(), name='api_manga_clean_lab'),
  path('manga-lab/translate/', api_views.MangaTranslateLabView.as_view(), name='api_manga_translate_lab'),
  ```

## 3. Plan de Validation
- Tests unitaires simulant le post d'une image et s'assurant que les bons services du conteneur sont appelés.
- Utilisation de mocks pour `inpaint_text_bubbles` et `translate_manga_page` afin de garantir que l'API renvoie bien le Base64 encapsulé dans un JSON structuré.
