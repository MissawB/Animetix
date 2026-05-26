from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class GraphPersistencePort(ABC):
    """
    Port (Interface) pour les opérations de persistance sur le graphe (Neo4j).
    Définit les contrats techniques et métier pour l'interaction avec le graphe.
    """

    @abstractmethod
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Exécute une requête Cypher brute."""
        pass

    @abstractmethod
    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Exécute une requête Cypher en mode lecture seule."""
        pass

    @abstractmethod
    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Exécute une requête Cypher en mode écriture."""
        pass

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

    @abstractmethod
    def sync_ai_extracted_graph(self, media_id: str, extracted_data: Dict[str, Any]) -> None:
        """Injecte les entités et relations extraites par l'IA."""
        pass

    @abstractmethod
    def sync_fan_theory(self, saga_name: str, theory_data: Dict[str, Any]) -> None:
        """Synchronise une théorie de fan pour une saga donnée."""
        pass

    @abstractmethod
    def sync_saga(self, saga_name: str, executive_summary: str, media_ids: List[str]) -> None:
        """Crée ou met à jour une saga et ses relations avec les médias."""
        pass

    @abstractmethod
    def sync_combat_lore(self, media_id: str, lore_data_list: List[Dict[str, Any]]) -> None:
        """Injecte les faits de combat extraits dans le graphe."""
        pass

    @abstractmethod
    def get_creator_network_context(self, person_name: str) -> str:
        """Récupère le contexte du réseau d'un créateur."""
        pass

    @abstractmethod
    def check_health(self) -> bool:
        """Vérifie la santé de la connexion au graphe."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Ferme la connexion au graphe."""
        pass

    @abstractmethod
    def sync_user_interaction(self, user_id: str, media_title: str, interaction_type: str) -> None:
        """Synchronise l'interaction et les préférences de l'utilisateur dans le graphe."""
        pass

    @abstractmethod
    def get_user_preferences_context(self, user_id: str) -> str:
        """Récupère un résumé textuel des préférences et de l'historique de l'utilisateur."""
        pass

    @abstractmethod
    def get_neighborhood(self, item_id: str, media_type: str, depth: int = 1) -> Dict[str, Any]:
        """Retrieves nodes and relationships within a certain depth."""
        pass

