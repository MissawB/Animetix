from abc import ABC, abstractmethod


class MlopsPort(ABC):
    @abstractmethod
    def log_dpo_preference(
        self, query: str, chosen: str, rejected: str, project_root: str
    ):
        """
        Journalise une paire de préférence DPO (Chosen vs Rejected) pour une requête donnée.
        """
        pass

    @abstractmethod
    def trigger_dpo_pipeline(self, min_samples: int = 100) -> dict:
        """Déclenche le pipeline Vertex AI de ré-entraînement DPO."""
        pass

    @abstractmethod
    def trigger_rag_pipeline(self) -> dict:
        """Déclenche le pipeline Vertex AI de ré-indexation RAG."""
        pass

    @abstractmethod
    def trigger_star_pipeline(self) -> dict:
        """Déclenche le pipeline Vertex AI de Fine-Tuning STaR LoRA."""
        pass

    @abstractmethod
    def list_pipeline_runs(
        self, pipeline_name: "str | None" = None, limit: int = 20
    ) -> list:
        """Liste les exécutions récentes de pipelines Vertex AI."""
        pass
