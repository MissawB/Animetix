# Design Doc: Réactivation de l'Audio Lab (Soundscape & Speech-to-Speech)

**Date:** 2026-06-08  
**Status:** Approved  
**Topic:** Réactiver les capacités de génération audio (Soundscape, S2S) via le backend.

## 1. Objectifs
- Fournir des endpoints API pour générer des ambiances sonores à partir de vidéos et permettre des interactions vocales directes.
- Intégrer les services `SoundscapeGenerationService` et `NativeSpeechLLMService` existants.
- Assurer la robustesse des entrées via une validation stricte des fichiers multimédias.

## 2. Architecture & Composants

### A. Vues API (`backend/api/animetix/api/labs.py`)

1. **`AudioLabDataView`** :
   - Endpoint: `GET /api/v1/labs/audio/`
   - Rôle: Retourne les métadonnées sur les outils audio (Soundscape, S2S, Voice Cloning).

2. **`SoundscapeGenerationView`** :
   - Endpoint: `POST /api/v1/labs/audio/soundscape/`
   - Payload: `multipart/form-data`
     - `video`: Fichier vidéo source.
   - Logique: Appelle `SoundscapeGenerationService.generate_soundscape_for_video(video_bytes)`.
   - Retour: URL ou Base64 de l'audio généré.

3. **`SpeechToSpeechLabView`** :
   - Endpoint: `POST /api/v1/labs/audio/s2s/`
   - Payload: `multipart/form-data`
     - `audio`: Entrée vocale utilisateur.
     - `persona`: (Optionnel) Prompt de persona pour la réponse.
   - Logique: Appelle `NativeSpeechLLMService.process_voice_interaction(audio_bytes, persona)`.
   - Retour: Données audio Base64 de la réponse.

### B. Routage (`backend/api/animetix/urls/api.py`)
- Ajouter les routes :
  ```python
  path('labs/audio/', api_views.AudioLabDataView.as_view(), name='api_audio_lab'),
  path('labs/audio/soundscape/', api_views.SoundscapeGenerationView.as_view(), name='api_audio_soundscape'),
  path('labs/audio/s2s/', api_views.SpeechToSpeechLabView.as_view(), name='api_audio_s2s'),
  ```

## 3. Plan de Validation
- Tests unitaires simulant des uploads valides et invalides.
- Vérification de la conversion correcte des résultats en formats consommables par le frontend (Base64 data URIs).
