# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md` et dans la section des succès.

## 🛠️ Dette Technique & Architecture

- [x] **Isolation réseau de la suite de tests** : Résoudre la fuite de requêtes réseau réelles dans les tests unitaires et d'intégration en migrant les mocks de `requests` vers de véritables mocks pour `httpx` (ou en utilisant `respx` ou en mockant `httpx.get` / `httpx.post` / `httpx.Client.get` / `httpx.AsyncClient.get`). Fichiers cibles :
  - `tests/adapters/test_fandom_adapter.py`
  - `tests/adapters/test_visual_reranker.py`
  - `tests/pipeline/test_advanced_scrapers.py`
  - `tests/pipeline/test_enrich_db_scraper.py`
  - `tests/pipeline/test_expert_scrapers.py`
  - `tests/pipeline/test_specialized_scrapers.py`

## 🧬 Fonctionnalités Créatives

- [ ] **Génération Structurée** : Passer du parsing JSON simple à une validation de schéma native plus robuste (via Instructor/Ollama).
- [ ] **Modération de contenu sémantique** : Étendre l'implémentation par mots-clés actuelle vers une approche sémantique (Llama Guard).
- [ ] **Diagnostics & Incertitude** : Implémenter `get_diagnostics` et `calculate_uncertainty` dans `InferencePort`.
