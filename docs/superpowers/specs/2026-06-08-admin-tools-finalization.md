# Design Doc: Finalisation des Outils d'Admin (Monitoring & MLOps)

**Date:** 2026-06-08  
**Status:** Approved  
**Topic:** Raccorder les pages de monitoring (`Admin DPO`, `SOTA Benchmarks`, `Graph Debugger`) aux services backend correspondants.

## 1. Objectifs
- Activer les endpoints backend pour le monitoring de l'alignement IA (DPO).
- Fournir les données de benchmarks SOTA réelles aux tableaux de bord frontend.
- Rendre opérationnel le "Graph Healer" pour la maintenance du Knowledge Graph Neo4j.
- Assurer la cohérence entre les appels `apiClient` du frontend et les routes Django.

## 2. Architecture & Composants

### A. DPO Curation (`backend/api/animetix/api/mlops.py`)
Le frontend attend un endpoint unique `POST /api/v1/mlops/dpo/curation/` pour soumettre une correction.
- **Action** : Transformer `DPOCurationViewSet` en `DPOCurationView` (APIView).
- **Service** : Ajouter la méthode `curate_feedback(feedback_id, chosen_text)` dans `DPOFeedbackLoop`. Cette méthode doit :
    1. Récupérer le `AIFeedback` original.
    2. Créer une instance de `GoldDatasetEntry` liée.
    3. Marquer l'entrée comme validée.

### B. SOTA Benchmarks (`backend/api/animetix/api/mlops.py`)
L'endpoint `GET /api/v1/mlops/sota/benchmarks/` doit renvoyer les données du `SOTABenchmarkService`.
- **Action** : Décommenter la route dans `urls/api.py`.
- **Données** : Assurer que le service renvoie les modèles 2026 (Llama 3.1, Claude 3.5, etc.) avec leurs scores ELO.

### C. Graph Debugger (`backend/api/animetix/api/graph.py`)
L'interface de diagnostic du Knowledge Graph utilise `GraphHealerService`.
- **Action** : Décommenter la route `POST /api/v1/graph/debugger/`.
- **Fonctionnalités** :
    - `GET` : Audit de qualité (nœuds isolés, conflits temporels).
    - `POST {action: 'cleanup'}` : Lancement du cycle `check_and_fix_broken_relations`.
    - `POST {action: 'heal', media_id: '...'}` : Reconstruction d'un nœud spécifique.

## 3. Routage (`backend/api/animetix/urls/api.py`)
Les routes suivantes seront activées et standardisées :
```python
path('mlops/dpo/curation/', api_views.DPOCurationView.as_view(), name='api_dpo_curation'),
path('mlops/sota/benchmarks/', api_views.SOTABenchmarkListView.as_view(), name='api_sota_benchmarks'),
path('graph/debugger/', api_views.GraphDebuggerView.as_view(), name='api_graph_debugger'),
```

## 4. Plan de Validation
- Tests unitaires pour la création de `GoldDatasetEntry` à partir d'un feedback.
- Mock de Neo4j pour vérifier que les actions de "Healing" sont correctement routées vers le service.
- Vérification que les types TypeScript générés correspondent aux nouveaux schémas de réponse.
