from abc import ABC, abstractmethod
from typing import Dict


class SyncPort(ABC):
    @abstractmethod
    def sync_to_vector_db(self, media_type: str, item_id: str, data: Dict):
        """Met à jour l'item dans ChromaDB."""
        pass

    @abstractmethod
    def sync_to_graph_db(self, media_type: str, item_id: str, data: Dict):
        """Met à jour l'item dans Neo4j."""
        pass
