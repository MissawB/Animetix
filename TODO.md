# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [/] **Fine-tune otaku — dataset assaini ✅ (PR #87) ; reste le réentraînement (bloqué GPU)** _(2026-07-13→17 ; détail cf. HISTORY 2026-07-17)_
  - **Reste** : réentraîner sur le dataset propre (`MissawB/otaku-expert-dataset`) **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké, aucun rebuild).

- [/] **Index visuel : phase 2 — `character_ccip_space` partiel, BLOQUÉ par la facturation GCP coupée** _(phase 1 2026-07-14 ; run tenté 2026-07-17, cf. HISTORY)_
  - **🔴 BLOQUEUR** : la facturation GCP du projet `animetix` a été **désactivée en plein run** (~13:15 ; log Brain « billing is disabled for this project »), Brain L4 tombé → job échoué après **~3,5 h de vecteurs écrits (préservés, reprenable)**. Cause probable : plafond de budget franchi par le run GPU. Impact : Brain + Cloud Run Jobs + prod bloqués.
  - **Reste (après rétablissement facturation, action console)** : 1) rouvrir la facturation sur `animetix` (vérifier/relever le plafond) ; 2) Brain `/health` = 200 ; 3) re-exécuter **par chunks** (`--limit N`) jusqu'aux ~35 000 ; 4) recherche perso ne renvoie plus 503.

## 🟡 Moyens

_Aucun item ouvert._

## 🟢 Faibles

- [x] **Brain — intégration Moshi (S2S local) : réécrite en cascade Kyutai STT + XTTS**
  - Remplacé le `from moshi.models import Moshi` fantôme par une cascade
    Kyutai STT (transformers, kyutai/stt-1b-en_fr-trfs) → LLM brain → XTTS-v2 (FR).
    Le paquet `moshi` a été écarté (il plafonne safetensors<0.8.0, incompatible avec
    diffusers==0.39.0) ; aucune nouvelle dépendance (transformers + coqui-tts déjà
    verrouillés). Contrat batch `speech_to_speech` inchangé ; Gemini Live intact.
    Implémentation dans [audio_mixin.py](backend/adapters/inference/audio_mixin.py)
    (`_load_stt`/`_transcribe`/`_synthesize`/`speech_to_speech`).
    Reste : rebuild/redeploy manuel de l'image brain (poids STT téléchargés au 1er
    appel), puis smoke test GPU (`S2S_GPU_SMOKE=1 pytest -m gpu`).
- [ ] **Frontend — plotly.js (~4,6 Mo) importé statiquement dans 8 pages** _(audit dette 2026-07-11)_
  - [AIUsagePage.tsx:18](frontend/src/pages/auth/AIUsagePage.tsx#L18), `LatentSpacePage`, `LiquidNeuralNetworkLabPage`, `StrategyLabPage`, `SeichijunreiMapPage`, `ArchetypeNexusPage`, `TransparencyPage`… Le chunk est isolé (`plotly-vendor`, [vite.config.ts:98](frontend/vite.config.ts#L98)) mais chaque visite télécharge 4,6 Mo — `AIUsagePage` n'affiche qu'un historique simple. + three.js dans 5 fichiers. **Reco** : lazy-import interne ou lib légère pour les graphes simples ; auditer via `stats.html` déjà généré.
- [ ] **Frontend — composants > 500 lignes (reliquat)** _(audit dette 2026-07-11 ; BlindtestPage découpé le 2026-07-16, cf. HISTORY)_
  - `BlindtestPage` traité (753→324, hook + sous-composants). Restent, à découper au fil de l'eau (sous-composants + hooks métier) : `TransparencyPage` (614), `AudioLabPage` (573), `LabHubPage` (569), `SpeechToSpeechLabPage` (544).
- [ ] **Deps — registre de prix désynchronisé (reliquat)** _(audit dette 2026-07-11 ; lock-doublons + COST_AUDIT réglés 2026-07-17)_
  - **Fait 2026-07-17** : lock backend vérifié — aiohttp/httpx/requests/ujson sont **tous transitifs** (via fsspec / datasets+diffusers / apache-beam+colpali / autobahn ; aucun dans [requirements.in](requirements.in)), donc **rien à dédupliquer** ; seul `orjson` est direct (légitime). [docs/COST_AUDIT.md](docs/COST_AUDIT.md) rafraîchi sur la vraie chaîne (Gemini 3.5 Flash + Qwen3.5 + brain-api ; chemin `deploy_brain.py` corrigé).
  - **Reste** : [`PricingService`](backend/core/domain/services/pricing_service.py) est désynchronisé — il tarifie `gpt-4o`/`gpt-3.5-turbo`/`claude-3-sonnet` (jamais appelés par la chaîne prod `[brain_api, google_genai]`) et n'a **aucune entrée `gemini-*`**, donc chaque appel Gemini live retombe sur le fallback `0.0` (facturé gratuit → attribution Bx fausse). Ajouter `gemini-3.5-flash` / `gemini-live-2.5-flash-native-audio` au registre + retirer les lignes OpenAI/Anthropic mortes.
