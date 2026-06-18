from abc import ABC, abstractmethod
from typing import Any, Dict


class EvalResultPort(ABC):
    """
    Port pour la persistence des résultats d'évaluation de l'IA (RAGas, etc.).
    """

    @abstractmethod
    def save_result(
        self, query: str, context: str, answer: str, metrics: Dict[str, Any]
    ) -> None:
        """
        Enregistre un résultat d'évaluation individuelle.

        Args:
            query (str): La requête utilisateur.
            context (str): Le contexte fourni au LLM.
            answer (str): La réponse générée par le LLM.
            metrics (Dict[str, Any]): Dictionnaire des scores (faithfulness, relevancy, etc.).
        """
        pass

    @abstractmethod
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques agrégées des évaluations (moyennes, taux d'hallucination).

        Returns:
            Dict[str, Any]: Un dictionnaire contenant les statistiques globales.
        """
        pass
