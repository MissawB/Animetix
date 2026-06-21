# TODO — Améliorations du projet Animetix

> Audit du 2026-06-21 (passe fraîche, 5 axes). Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).
>
> _Note de vérification : le `.env` contenant de vraies clés n'est PAS suivi par git (gitignored, jamais commité) — pas de fuite dans le dépôt, pas de rotation d'urgence. `error_latent.html` et `.coverage` ne sont pas suivis non plus._

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [ ] **Repo — 125 Mo de données suivies dans git** _(vérifié)_
  - `data/processed/filtered_characters.json` (40 Mo), `refined_characters.json` (30 Mo), `clean_characters.json` (24 Mo), etc. Artefacts générés qui gonflent l'historique et ralentissent les clones.
  - Migrer vers Git LFS **ou** `git rm --cached` + régénération au build ; documenter le téléchargement dans le README.
- [ ] **Sécu — `exec()` sur du code généré par LLM (surface RCE)**
  - [self_evolving_compiler.py:62](backend/core/domain/services/self_evolving_compiler.py#L62) exécute du source dynamique (`# nosec B102`). Une injection de prompt en amont permettrait l'exécution de code arbitraire.
  - Valider l'AST avant exécution (interdire `import`/`os`/`subprocess`), sandboxer (RestrictedPython), ou désactiver la feature en prod.
- [ ] **Archi — violations de la frontière hexagonale (domaine → infra)**
  - Le cœur importe l'ORM Django : [manga_service.py:5](backend/core/domain/services/manga_service.py#L5), [voice_ingestion_service.py:6](backend/core/domain/services/voice_ingestion_service.py#L6) ; [llm_service.py:58](backend/core/domain/services/llm_service.py#L58) reach dans `animetix.middleware`.
  - Injecter un port/repository ; passer `user_id`/`tier` en paramètres au lieu de lire le middleware.
- [ ] **Archi — code de test (Mock/MagicMock) dans un service de prod**
  - [agentic_rag_service.py:58-104](backend/core/domain/services/agentic_rag_service.py#L58) reconstruit des agents pour les mocks dans `__init__`. Fragile, ne devrait jamais tourner en prod.
  - Sortir la logique mock vers des fixtures de test.

## 🟡 Moyens

- [ ] **API — fuite de stacktrace + permission par défaut trop ouverte**
  - `return Response({"error": str(e)}, status=500)` expose l'exception au client : [labs.py:1021](backend/api/animetix/api/labs.py#L1021), [core.py:196](backend/api/animetix/api/core.py#L196) → `logger.exception()` + message générique.
  - Permission DRF par défaut = `IsAuthenticatedOrReadOnly` ([settings.py:250](backend/api/animetix_project/settings.py#L250)) : tout lisible sans auth sauf override → passer à `IsAuthenticated` par défaut, `AllowAny` ciblé.
- [ ] **Backend — `except Exception:` trop larges + constantes dupliquées**
  - Nombreux catch-all génériques masquant les vrais bugs → resserrer sur des exceptions spécifiques.
  - `MAX_IMAGE_SIZE` / allow-lists MIME dupliquées entre [labs.py](backend/api/animetix/api/labs.py) et [core.py](backend/api/animetix/api/core.py) → centraliser dans `backend/core/constants.py`.
- [ ] **Backend — `UnifiedInferenceAdapter` god object**
  - 8 mixins, ~476 lignes ([unified_inference_adapter.py:30](backend/adapters/inference/unified_inference_adapter.py#L30)) ; MRO fragile, dur à tester → composition plutôt qu'héritage multiple.
- [ ] **Frontend — `fetch()` brut qui contourne `apiClient`**
  - [SearchBar.tsx:81](frontend/src/components/SearchBar.tsx#L81) et [AudioLabPage.tsx:127](frontend/src/pages/labs/AudioLabPage.tsx#L127) bypassent CSRF + auth Firebase + toasts → tout passer par `apiClient`.
- [ ] **Frontend — état local fragmenté**
  - [AudioLabPage.tsx:64](frontend/src/pages/labs/AudioLabPage.tsx#L64) (~13 `useState`) ; anti-pattern `JSON.stringify` en render dans [SynapticLabPage.tsx:110](frontend/src/pages/labs/SynapticLabPage.tsx#L110) → `useReducer`/hook dédié.
- [ ] **CI — gaspillage et robustesse**
  - Pas de `concurrency: cancel-in-progress` → runs redondants empilés.
  - PyTorch (~800 Mo) réinstallé sans cache dans 3 jobs ([ci.yml](.github/workflows/ci.yml) ~97/163/203).
  - Pas de `timeout-minutes` sur `perf-test`/`integration-test`.
  - À confirmer : `--cov-fail-under=75` ([ci.yml:119](.github/workflows/ci.yml#L119)) annoncé comme *hard gate* bloquant le deploy — vérifier la cohérence avec la couverture réelle.

## 🟢 Faibles

- [ ] **A11y & logs frontend** : `<img>` sans `alt`, boutons admin sans `aria-label`, `console.error` laissés en prod (~41 fichiers).
- [ ] **Deps** : doublon `opencv-python` + `opencv-python-headless` ([requirements.txt:580](requirements.txt#L580)) ; GCP / `transformers` peu ou pas pinnés dans [requirements.in](requirements.in) (build non reproductible).
- [ ] **DX** : pas de Prettier ni `.editorconfig` ; badge README « Python 3.11+ » alors que CI/pyproject ciblent 3.12.
- [ ] **Couverture frontend — élargir** _(outillage + CI faits ; ~29 % stmts, 492 tests — cf. [HISTORY](docs/HISTORY.md))_
  - Optionnel / ROI décroissant : couvrir les flows complexes restants (3D/canvas/WebSocket) et remonter le plancher de seuils au fil de l'eau.
- [ ] **Organisation des tests backend — consolidation physique** _(convention documentée dans `tests/README.md` ; cf. [HISTORY](docs/HISTORY.md))_
  - **Différé** jusqu'au merge de `coverage-consolidation` (écrit activement dans `tests/`) : fusionner `tests/backend/core`→`tests/core`, `tests/backend/api`→`tests/api`, `tests/pipeline_logic`→`tests/pipeline`. Gain fonctionnel nul (découverte via `testpaths=tests`), à faire en une passe hors activité parallèle.
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. À purger lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).
