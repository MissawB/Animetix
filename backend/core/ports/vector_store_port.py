from abc import ABC, abstractmethod
from typing import Dict, List


class VectorStorePort(ABC):
    """Port de lecture d'un magasin de vecteurs (embeddings).

    Abstrait le client de la base vectorielle (pgvector/AlloyDB) afin que le
    `core` ne dépende pas de la couche `pipeline`/infrastructure.
    """

    @abstractmethod
    def get_embeddings(self, collection_name: str, limit: int) -> List[List[float]]:
        """Retourne jusqu'à `limit` embeddings d'une collection.

        Retourne une liste vide si la collection est absente ou vide.
        """
        ...

    @abstractmethod
    def search_by_vector(
        self, collection_name: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict]:
        """Retourne les `limit` éléments les plus proches de `query_vector`.

        Chaque élément est un dict de métadonnées augmenté de sa clé ``id``.
        Retourne une liste vide si la collection est absente ou en cas d'erreur.
        """
        ...
