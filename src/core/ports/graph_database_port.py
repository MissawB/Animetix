from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class GraphDatabasePort(ABC):
    """
    Port (Interface) pour les opérations sur la base de données de graphe (ex: Neo4j).
    Définit les besoins du domaine sans dépendre d'une implémentation concrète.
    """
    
    @abstractmethod
    def find_logical_connections(self, media_id: str) -> List[Dict[str, Any]]:
        """Trouve les médias connectés logiquement dans le graphe."""
        pass

    @abstractmethod
    def get_community_summary(self, category_type: str, category_name: str) -> str:
        """Récupère une vue d'ensemble d'une communauté."""
        pass

    @abstractmethod
    def multi_hop_traversal(self, start_node: str, steps: List[str]) -> str:
        """Navigue sur un chemin défini dans le graphe."""
        pass

    @abstractmethod
    def get_enriched_context(self, media_ids: List[str]) -> str:
        """Récupère un contexte enrichi pour une liste de médias."""
        pass

    @abstractmethod
    def sync_media_to_graph(self, media_item: Any, media_type: str) -> None:
        """Injecte une œuvre et ses relations de base."""
        pass
