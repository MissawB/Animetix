# Design Doc: Réactivation du Video Lab (FateZero Style Transfer)

**Date:** 2026-06-08  
**Status:** Approved  
**Topic:** Réactiver le transfert de style vidéo SOTA (type FateZero) via le backend.

## 1. Objectifs
- Exposer la capacité de transfert de style vidéo temporellement consistant via une API.
- Permettre aux utilisateurs de transformer des vidéos réelles en styles d'animation célèbres (Ufotable, Ghibli, Shaft, Kyoto).
- Garantir que le pipeline utilise la consistance par attention native du `diffusers_adapter`.

## 2. Architecture & Composants

### A. Vues API (`backend/api/animetix/api/labs.py`)

1. **`VideoFateZeroLabView`** :
   - Endpoint: `POST /api/v1/video-lab/fatezero/`
   - Payload: `multipart/form-data`
     - `video`: Le fichier vidéo à transformer.
     - `studio_style`: Nom du studio cible (ex: "Ghibli").
   - Logique:
     1. Lit les octets du fichier vidéo.
     2. Appelle `container.core.studio_transform_service().transform_video_to_anime_sota(video_bytes, studio_style)`.
   - Retour: JSON contenant le `video_url` ou le chemin du résultat.

2. **`VideoLabDataView`** :
   - Endpoint: `GET /api/v1/video-lab/`
   - Retour: Liste des outils disponibles (FateZero) et des styles supportés.

### B. Routage (`backend/api/animetix/urls/api.py`)
- Ajouter les routes :
  ```python
  path('labs/video/', api_views.VideoLabDataView.as_view(), name='api_video_lab'),
  path('labs/video/fatezero/', api_views.VideoFateZeroLabView.as_view(), name='api_video_fatezero_lab'),
  ```

## 3. Plan de Validation
- Test unitaire : Poster une vidéo bidon et vérifier que le service de transformation est invoqué avec les bons paramètres.
- Vérification que les styles inconnus retombent sur un style par défaut via le service du domaine.
