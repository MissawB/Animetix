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

        Une liste vide signifie « la requête a tourné et n'a rien trouvé », et
        UNIQUEMENT ça. Une panne (collection injoignable, requête refusée)
        DOIT lever `InfrastructureError` — jamais rendre `[]`. L'appelant
        facture avant de chercher : une panne rendue comme « aucun résultat »
        fait payer l'utilisateur pour une recherche qui n'a jamais eu lieu, et
        ne laisse aucune trace dans la réponse.
        """
        ...

    @abstractmethod
    def get_collection_count(self, collection_name: str) -> int:
        """Retourne le nombre de vecteurs dans une collection (0 si absente).

        Sert de garde-fou avant facturation : une recherche contre une
        collection vide ne peut jamais retourner de résultat.
        """
        ...
