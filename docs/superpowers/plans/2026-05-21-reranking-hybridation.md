# Reranking Sémantique & Hybridation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter un véritable Reranking sémantique avec un modèle Cross-Encoder, standardiser l'interface d'inférence (Port) et nettoyer le service RAG.

**Architecture:** Ajout de `rerank_documents` dans `InferencePort`. Implémentation via `TransformersAdapter` avec un chargement paresseux (`lazy_import`) de `sentence_transformers`. Refactorisation de `AdvancedRAGService` pour dépendre du port d'inférence au lieu d'un objet "reranker" générique non typé.

**Tech Stack:** Python 3.10+, sentence-transformers, Pytest.

---

### Task 1: Mettre à jour l'Interface InferencePort

**Files:**
- Modify: `backend/core/ports/inference_port.py`

- [ ] **Step 1: Ajouter la signature `rerank_documents` à `InferencePort`**
Dans le fichier `backend/core/ports/inference_port.py`, ajouter la méthode suivante dans la classe `InferencePort` (par exemple après `generate_structured`) :

```python
    @abstractmethod
    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Évalue la pertinence de plusieurs documents par rapport à une requête (Cross-Encoder)."""
        pass
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/ports/inference_port.py
git commit -m "feat(core): add rerank_documents to InferencePort"
```

---

### Task 2: Implémenter `rerank_documents` dans TransformersAdapter

**Files:**
- Modify: `backend/adapters/inference/transformers_adapter.py`

- [ ] **Step 1: Implémenter la méthode**
Dans `backend/adapters/inference/transformers_adapter.py`, ajouter l'implémentation de `rerank_documents`.

```python
    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Implémentation du reranking avec sentence_transformers."""
        if not documents:
            return []
            
        from core.utils.lazy_import import lazy_import
        sentence_transformers = lazy_import('sentence_transformers')
        
        # Singleton pour le reranker afin d'éviter de le recharger
        if not hasattr(self, '_cross_encoder'):
            # Utilisation du modèle BGE-reranker ou ms-marco par défaut
            self._cross_encoder = sentence_transformers.CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
        pairs = [[query, doc] for doc in documents]
        scores = self._cross_encoder.predict(pairs)
        
        # S'assurer que le retour est bien une liste de floats
        return [float(score) for score in scores]
```

- [ ] **Step 2: Mettre à jour FallbackAdapter**
Dans `backend/adapters/inference/fallback_adapter.py`, ajouter `rerank_documents` dans la classe `FallbackAdapter` pour cascader vers le `primary_adapter` :

```python
    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        if hasattr(self.primary_adapter, 'rerank_documents'):
            try:
                return self.primary_adapter.rerank_documents(query, documents)
            except Exception as e:
                import logging
                logger = logging.getLogger("animetix")
                logger.warning(f"Primary reranker failed: {e}. Falling back to default scoring (0.0).")
                return [0.0] * len(documents)
        from core.ports.inference_port import InferenceNotImplementedError
        raise InferenceNotImplementedError("Reranking not supported by current primary adapter")
```

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/transformers_adapter.py backend/adapters/inference/fallback_adapter.py
git commit -m "feat(adapters): implement rerank_documents in Transformers and Fallback adapters"
```

---

### Task 3: Refactoriser AdvancedRAGService

**Files:**
- Modify: `backend/core/domain/services/advanced_rag_service.py`

- [ ] **Step 1: Nettoyer le constructeur**
Modifier `__init__` pour supprimer la dépendance directe à `reranker` :

```python
    def __init__(self, repository: RepositoryPort, llm_service: LLMService, neo4j_manager=None, prompt_manager: PromptManager = None):
        self.repository = repository
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.prompt_manager = prompt_manager or getattr(llm_service, 'prompt_manager', None)
        self._indices: Dict[str, HybridSearchIndex] = {}
```

- [ ] **Step 2: Refactoriser `rerank_results`**
Modifier `rerank_results` pour utiliser le port d'inférence. Remplacer `from core.utils.lazy_import import lazy_import` ou `import torch` si présent dans cette méthode par l'appel à l'adaptateur.

```python
    def rerank_results(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """Ré-ordonne les candidats en utilisant le modèle de cross-encoding de l'InferencePort."""
        if not candidates:
            return candidates
        
        texts_to_score = []
        for c in candidates:
            graph_info = ""
            if self.neo4j_manager:
                try:
                    connections = self.neo4j_manager.find_logical_connections(c['id'])
                    if connections:
                        graph_info = " | Connexions: " + ", ".join([f"{conn['title']} ({conn['strength']})" for conn in connections])
                except Exception as e:
                    logger.warning(f"Neo4j enrichment failed: {e}")
            
            doc_text = f"Titre: {c.get('title') or c.get('name')} | Description: {c.get('description', '')[:300]}{graph_info}"
            texts_to_score.append(doc_text)
            
        try:
            scores = self.llm_service.inference_engine.rerank_documents(query, texts_to_score)
            ranked_indices = np.argsort(scores)[::-1]
            return [candidates[i] for i in ranked_indices]
        except Exception as e:
            logger.error(f"Reranking via InferencePort failed: {e}")
            return candidates
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/advanced_rag_service.py
git commit -m "refactor(domain): use InferencePort for reranking in AdvancedRAGService"
```

---

### Task 4: Mettre à jour les tests unitaires

**Files:**
- Modify: `tests/core/test_advanced_rag_service.py`

- [ ] **Step 1: Ajuster l'initialisation dans les tests**
Ouvrir `tests/core/test_advanced_rag_service.py`. Enlever tout passage d'un mock `reranker` à l'initialisation de `AdvancedRAGService`.

- [ ] **Step 2: Mocker `rerank_documents`**
Ajouter ou modifier un test pour vérifier le reranking :

```python
def test_rerank_results_with_inference_port(mocker):
    from core.domain.services.advanced_rag_service import AdvancedRAGService
    from core.domain.services.llm_service import LLMService
    from core.ports.repository_port import RepositoryPort
    from core.ports.inference_port import InferencePort
    
    # Mocks
    mock_repo = mocker.Mock(spec=RepositoryPort)
    mock_inference = mocker.Mock(spec=InferencePort)
    mock_inference.rerank_documents.return_value = [0.1, 0.9, 0.5]
    
    mock_llm_service = mocker.Mock(spec=LLMService)
    mock_llm_service.inference_engine = mock_inference
    
    service = AdvancedRAGService(repository=mock_repo, llm_service=mock_llm_service)
    
    candidates = [
        {'id': '1', 'title': 'Bad Match'},
        {'id': '2', 'title': 'Best Match'},
        {'id': '3', 'title': 'Medium Match'}
    ]
    
    ranked = service.rerank_results("query", candidates)
    
    assert len(ranked) == 3
    assert ranked[0]['id'] == '2'  # Highest score (0.9)
    assert ranked[1]['id'] == '3'  # Second highest (0.5)
    assert ranked[2]['id'] == '1'  # Lowest score (0.1)
    mock_inference.rerank_documents.assert_called_once()
```

- [ ] **Step 3: Lancer le test**

Run: `pytest tests/core/test_advanced_rag_service.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/core/test_advanced_rag_service.py
git commit -m "test(core): update advanced_rag_service tests for new reranking logic"
```
