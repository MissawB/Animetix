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

- [ ] **Couverture frontend — élargir** _(outillage + CI faits ; ~29 % stmts, 492 tests — cf. [HISTORY](docs/HISTORY.md))_
  - Optionnel / ROI décroissant : couvrir les flows complexes restants (3D/canvas/WebSocket) et remonter le plancher de seuils au fil de l'eau.
- [ ] **Organisation des tests backend — consolidation physique** _(convention documentée dans `tests/README.md` ; cf. [HISTORY](docs/HISTORY.md))_
  - **Différé** jusqu'au merge de `coverage-consolidation` (écrit activement dans `tests/`) : fusionner `tests/backend/core`→`tests/core`, `tests/backend/api`→`tests/api`, `tests/pipeline_logic`→`tests/pipeline`. Gain fonctionnel nul (découverte via `testpaths=tests`), à faire en une passe hors activité parallèle.
