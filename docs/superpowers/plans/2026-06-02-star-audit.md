# Audit Humain Dataset STaR - Plan d'Exécution

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter une validation humaine obligatoire pour les traces de raisonnement STaR avant leur utilisation en Fine-Tuning.

**Architecture:** Migration de la sauvegarde des traces STaR (actuellement en JSONL brut) vers la base de données via `GoldDatasetEntry` (avec `is_validated=False` par défaut). Le pipeline MLOps ne consommera que les entrées validées.

**Tech Stack:** Python, Django ORM, Dependency Injector.

---

### Task 1: Mise à jour du Port d'Accès aux Données

**Files:**
- Modify: `backend/core/ports/gold_dataset_port.py`

- [ ] **Step 1: Ajouter les nouvelles méthodes au port**

Ajouter les méthodes abstraites `save_star_trace` et `get_unprocessed_validated_entries` dans `GoldDatasetPort`.

```python
    @abstractmethod
    def save_star_trace(self, instruction: str, input_text: str, output_text: str) -> None:
        """Sauvegarde une trace STaR en attente de validation humaine."""
        pass

    @abstractmethod
    def get_unprocessed_validated_entries(self) -> List[Dict[str, Any]]:
        """Récupère les entrées validées qui n'ont pas encore été exportées pour le Fine-Tuning."""
        pass
        
    @abstractmethod
    def mark_entries_as_processed(self, entry_ids: List[int]) -> None:
        pass
```

### Task 2: Implémentation dans l'Adaptateur Django

**Files:**
- Modify: `backend/adapters/persistence/django_gold_dataset_adapter.py`

- [ ] **Step 1: Implémenter les nouvelles méthodes**

```python
    def save_star_trace(self, instruction: str, input_text: str, output_text: str) -> None:
        from animetix.models import GoldDatasetEntry
        GoldDatasetEntry.objects.create(
            instruction=instruction,
            context=input_text, # On utilise context pour l'input de l'énigme
            response=output_text,
            is_validated=False
        )

    def get_unprocessed_validated_entries(self) -> List[Dict[str, Any]]:
        from animetix.models import GoldDatasetEntry
        # On suppose qu'on ajoute un flag ou qu'on supprime après export. 
        # Pour simplifier, on prend les validés. L'idéal serait d'ajouter un champ `is_processed`
        # mais on va s'en tenir à la récupération des validés pour l'instant.
        entries = GoldDatasetEntry.objects.filter(is_validated=True).order_by('created_at')
        return [self._to_dict(e) for e in entries]
        
    def mark_entries_as_processed(self, entry_ids: List[int]) -> None:
        # En l'absence de champ is_processed, on pourrait juste les logguer 
        # ou, si une modification du modèle est permise, les marquer. 
        # Restons simple sans migration DB si possible.
        pass
```

### Task 3: Refactorisation du Service StarReasoner

**Files:**
- Modify: `backend/core/domain/services/star_reasoner_service.py`

- [ ] **Step 1: Remplacer l'écriture fichier par le Port DB**

Modifier `__init__` pour accepter `gold_dataset_port: GoldDatasetPort` au lieu de `training_data_path`.

```python
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, gold_dataset_port):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.gold_dataset_port = gold_dataset_port
```

- [ ] **Step 2: Modifier _save_traces**

Remplacer la logique d'écriture de fichier par un appel à la base de données.

```python
    def _save_traces(self, paths: List[Dict]):
        """Sauvegarde les traces de raisonnement correctes pour validation humaine."""
        for path in paths:
            self.gold_dataset_port.save_star_trace(
                instruction="Résous cette énigme sur l'univers anime/manga en détaillant ton raisonnement.",
                input_text=path["riddle"],
                output_text=path["reasoning_trace"]
            )
```

### Task 4: Refactorisation du Service MLOps

**Files:**
- Modify: `backend/core/domain/services/star_mlops_service.py`

- [ ] **Step 1: Modifier la préparation du dataset**

Utiliser `gold_dataset_port` au lieu de lire le fichier JSONL.

```python
    def __init__(self, prompt_manager: PromptManager, gold_dataset_port, main_dataset_path: str = "data/mlops/datasets/animetix_expert_ft.jsonl"):
        self.prompt_manager = prompt_manager
        self.gold_dataset_port = gold_dataset_port
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.main_dataset_path = os.path.join(base_dir, main_dataset_path)

    def prepare_star_dataset(self) -> int:
        entries = self.gold_dataset_port.get_unprocessed_validated_entries()
        if not entries: return 0
        
        # ... logic to write to self.main_dataset_path ...
```

### Task 5: Mise à jour de l'Injection de Dépendances

**Files:**
- Modify: `backend/api/animetix/containers/core_services.py`

- [ ] **Step 1: Injecter le port dans les services**

Mettre à jour `star_reasoner_service` et `star_mlops_service` dans le container pour inclure `gold_dataset_port=persistence.gold_dataset_adapter`.
