# GEMINI - Mandats du Projet Animetix

Ce fichier définit les règles absolues et les contraintes techniques du workspace.

> [!IMPORTANT]
> Des instructions spécifiques sont disponibles pour les sous-domaines :
> - [Mandats Backend](../backend/GEMINI.md)
> - [Mandats Frontend](../frontend/GEMINI.md)

## 🏗️ Architecture Hexagonale (Ports & Adapters)
Toute modification doit respecter strictement la séparation des couches :

- **Domain (Core) :** `backend/core/domain/`. Logique métier pure, sans dépendance externe.
    - *Entities:* Utiliser `Pydantic` pour la validation de structure (`ai_schemas.py`).
    - *Services:* Logique de haut niveau. Interdiction d'utiliser `print`, utiliser le module `logging`.
- **Ports (Interfaces) :** `backend/core/ports/`. Définitions abstraites des capacités externes.
- **Adapters (Infrastructure) :** `backend/adapters/`. Implémentations concrètes.
    - *Persistence:* `UnifiedRepositoryAdapter` (ChromaDB).
    - *Inference:* `FallbackInferenceAdapter` (LLM Resilience + Streaming).
- **Presentation (Driving) :** `backend/api/`. Django Headless API. Validation obligatoire via `Django Forms` pour les entrées utilisateur.

## 📝 Standards de Code & IA
- **Typing :** Python 3.10+. Annotations de type strictes obligatoires sur toutes les fonctions.
- **Logging :** Loggers nommés (`animetix.rag`). Niveaux : `info`, `warning`, `error`.
- **Prompts :** ZERO prompt en dur. Utilisation exclusive de `PromptManager` (fichiers YAML).
- **Sécurité :** Désinfection systématique des sorties IA avec le filtre `sanitize_ai`.

## 🚀 Spécificités Workspace & MLOps
- **Pipeline :** Respecter les patterns Dagster. Synchronisation Neo4j automatisée.
- **Observability :** 
    - Tracking systématique des tokens/coûts via `UsagePort`.
    - Évaluation RAG via `Ragas` (Faithfulness, Relevance).
- **SOTA Search :** Avant de choisir/mettre à jour un modèle, utiliser `huggingface-best` pour identifier le meilleur candidat actuel.
- **Performance :** Pagination côté DB (`limit`/`offset`). Index HNSW pour les vecteurs.

## 🛠️ Workflow d'Intervention
1. **Research :** Mapper les changements aux couches Domain, Port ou Adapter.
2. **Strategy :** Justifier le respect de l'intégrité hexagonale et du typage.
3. **Execution :** Mise à jour chirurgicale + Ajout de tests dans `tests/`.
4. **Validation :** Exécuter `pytest` et vérifier l'étanchéité des couches.
