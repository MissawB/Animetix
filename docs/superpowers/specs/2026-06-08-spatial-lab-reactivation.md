# Design Doc: Réactivation du Spatial Lab (3D & Profondeur)

**Date:** 2026-06-08  
**Status:** Approved  
**Topic:** Réactiver les capacités de calcul spatial (3D Gaussian Splatting) via le backend.

## 1. Objectifs
- Fournir des endpoints API pour transformer des images 2D et des clips vidéo en scènes 3D navigables.
- Intégrer les services `SpatialComputingService` et `CinematicVolumetricReconstructionService` existants.
- Exposer des métadonnées pour que le frontend puisse configurer les viewers appropriés.

## 2. Architecture & Composants

### A. Vues API (`backend/api/animetix/api/labs.py`)

1. **`SpatialLabDataView`** :
   - Endpoint: `GET /api/v1/labs/spatial/`
   - Rôle: Retourne la liste des outils (Image-to-3D, Cinematic Reconstruction).

2. **`Generate3DDataView`** :
   - Endpoint: `POST /api/v1/labs/spatial/generate-3d/`
   - Payload: `multipart/form-data`
     - `image`: Le fichier image (poster, screenshot).
     - `title`: (Optionnel) Titre de la scène.
   - Logique: Appelle `SpatialComputingService.reconstruct_3d_scene(image_bytes, title)`.
   - Retour: URL du modèle PLY et type de viewer (`gaussian_splatting`).

3. **`CinematicReconstructionView`** :
   - Endpoint: `POST /api/v1/labs/spatial/cinematic/`
   - Payload: `multipart/form-data`
     - `video`: Le clip vidéo anime.
     - `title`: (Optionnel) Titre de la séquence.
   - Logique: Appelle `CinematicVolumetricReconstructionService.reconstruct_dynamic_cinematic_scene(video_bytes, title)`.
   - Retour: Liste de frames 3D avec timestamps et URLs.

### B. Routage (`backend/api/animetix/urls/api.py`)
- Ajouter les routes :
  ```python
  path('labs/spatial/', api_views.SpatialLabDataView.as_view(), name='api_spatial_lab'),
  path('labs/spatial/generate-3d/', api_views.Generate3DDataView.as_view(), name='api_generate_3d'),
  path('labs/spatial/cinematic/', api_views.CinematicReconstructionView.as_view(), name='api_cinematic_reconstruction'),
  ```

## 3. Plan de Validation
- Tests unitaires avec mocks des modèles d'inférence (Depth & 3D Splatting).
- Vérification que les fichiers multipart sont correctement lus et passés sous forme de `bytes` aux services du domaine.
