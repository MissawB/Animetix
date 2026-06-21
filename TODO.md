# TODO — Améliorations du projet Animetix

> Audit du 2026-06-20. Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [ ] **CI couverture — job d'intégration optionnel** _(le gate `--cov-fail-under=75` + upload Codecov sont posés)_
  - Hook `conftest` qui ping ollama et **skip gracieusement** les tests `@pytest.mark.integration` s'il est injoignable, + job CI dédié non-bloquant.

## 🟡 Moyens

_Rien d'ouvert._

## 🟢 Faibles

- [x] **Sécu image — CVEs OS de la base Debian** _(zlib/openssl/sqlite3/krb5/pam/perl… — surtout low / no-known-exploit)_
  - **Cause racine corrigée** : le build prod (`cloudbuild.yaml`) faisait `--cache-from web:latest` **sans `--pull`** → la couche de base (`python:3.12-slim-bookworm` + `apt-get`) était réutilisée du cache, donc les **correctifs de sécurité Debian n'étaient jamais appliqués**. Ajout de `--pull` (cloudbuild web + brain + build de validation CI) → chaque déploiement re-tire la base patchée. Le résiduel (CVEs non encore corrigées par Debian, low/no-exploit) est accepté.
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502, CVSS 8.6) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous (pas de désérialisation d'input non fiable). Le reste du scan Snyk était **périmé** (django/pillow/urllib3/… déjà à jour). À purger **uniquement** lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).

- [ ] **Couverture frontend — élargir** _(outillage + CI faits ; ~29 % stmts, 492 tests — cf. [HISTORY](docs/HISTORY.md))_
  - Optionnel / ROI décroissant : couvrir les flows complexes restants (3D/canvas/WebSocket) et remonter le plancher de seuils au fil de l'eau.
- [ ] **Organisation des tests backend — consolidation physique** _(convention documentée dans `tests/README.md` ; cf. [HISTORY](docs/HISTORY.md))_
  - **Différé** jusqu'au merge de `coverage-consolidation` (écrit activement dans `tests/`) : fusionner `tests/backend/core`→`tests/core`, `tests/backend/api`→`tests/api`, `tests/pipeline_logic`→`tests/pipeline`. Gain fonctionnel nul (découverte via `testpaths=tests`), à faire en une passe hors activité parallèle.
