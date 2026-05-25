from abc import ABC, abstractmethod

class MlopsPort(ABC):
    @abstractmethod
    def log_dpo_preference(self, query: str, chosen: str, rejected: str, project_root: str):
        """
        Journalise une paire de préférence DPO (Chosen vs Rejected) pour une requête donnée.
        """
        pass
