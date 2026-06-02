# Design Spec : Phase 1 - Reranking Sémantique & Hybridation Avancée

## 1. Objectif
Améliorer drastiquement la pertinence de la recherche du RAG (Retrieval-Augmented Generation) en standardisant la recherche hybride et en implémentant un véritable modèle Cross-Encoder pour le réordonnancement (Reranking). Le tout en respectant l'architecture hexagonale du projet (Ports & Adapters).

## 2. État Actuel & Problèmes
- L'`AdvancedRAGService` tente d'utiliser `self.reranker.predict()`. Cela suppose l'injection directe d'un modèle (fuite de la logique d'infrastructure dans le domaine métier).
- Le RRF (Reciprocal Rank Fusion) de `HybridSearchIndex` est implémenté statiquement mais peut être mieux interconnecté avec la nouvelle couche de Reranking.
- L'infrastructure d'inférence (`InferencePort`) ne possède pas de contrat formel pour le Reranking.

## 3. Architecture & Implémentation

### 3.1. Couche Port (`core/ports/inference_port.py`)
Ajout d'un nouveau contrat dans l'interface `InferencePort` :
```python
@abstractmethod
def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
    """Évalue la pertinence de plusieurs documents par rapport à une requête (Cross-Encoder)."""
    pass
```

### 3.2. Couche Adapter (`adapters/inference/transformers_adapter.py` / `fallback_adapter.py`)
- Implémentation de `rerank_documents` en utilisant `sentence_transformers.CrossEncoder`.
- Utilisation de `lazy_import('sentence_transformers')` pour ne pas ralentir le chargement global.
- Choix de modèle par défaut (SOTA léger) : `BAAI/bge-reranker-base` ou `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- Si le port n'implémente pas le reranking (ex: API externe non compatible), levée de `InferenceNotImplementedError`.

### 3.3. Couche Domaine (`core/domain/services/advanced_rag_service.py`)
- Suppression de l'attribut `self.reranker` du constructeur (qui brisait l'architecture hexagonale).
- Utilisation directe de `self.llm_service.inference_engine.rerank_documents(query, texts)` pour récupérer les scores.
- Traitement robuste des erreurs : en cas de `InferenceNotImplementedError` ou de plantage, on bascule gracieusement sur les résultats non réordonnés (graceful fallback).

## 4. Stratégie de Test
- Créer/Mettre à jour les tests unitaires pour `AdvancedRAGService` mockant `rerank_documents`.
- S'assurer que le pipeline Dagster ne casse pas si le modèle de Reranking n'est pas encore téléchargé (le Lazy Import + gestion d'erreurs garantissent cela).

## 5. Résultat Attendu
La pertinence des documents récupérés (le contexte injecté dans le RAG) sera grandement améliorée, car le Cross-Encoder analyse l'interaction sémantique entre la requête et le document simultanément, contrairement au Vector Search classique.
