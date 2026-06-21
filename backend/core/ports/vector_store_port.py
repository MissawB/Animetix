from abc import ABC, abstractmethod
from typing import List


class VectorStorePort(ABC):
    """Port de lecture d'un magasin de vecteurs (embeddings).

    Abstrait le client de la base vectorielle (Chroma, pgvector…) afin que le
    `core` ne dépende pas de la couche `pipeline`/infrastructure.
    """

    @abstractmethod
    def get_embeddings(self, collection_name: str, limit: int) -> List[List[float]]:
        """Retourne jusqu'à `limit` embeddings d'une collection.

        Retourne une liste vide si la collection est absente ou vide.
        """
        ...
