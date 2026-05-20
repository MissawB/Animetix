import logging
import numpy as np
from typing import Dict

logger = logging.getLogger("animetix.scoring")

class ScoringDomainService:
    """
    Service centralisant la logique métier liée aux calculs de scores,
    systèmes de pondération et filtrage complexe (ex-utils).
    """
    
    @staticmethod
    def calculate_animetix_ragas_score(metrics: Dict[str, float]) -> float:
        """
        Calcule une note globale sur 10 basée sur les métriques RAGAS.
        Poids métier : Faithfulness (40%), Relevancy (30%), Context Recall (30%)
        """
        f = metrics.get('faithfulness', 0)
        r = metrics.get('answer_relevancy', 0)
        cr = metrics.get('context_recall', 0)
        
        f = 0 if f is None or np.isnan(f) else f
        r = 0 if r is None or np.isnan(r) else r
        cr = 0 if cr is None or np.isnan(cr) else cr
        
        score = (f * 0.4 + r * 0.3 + cr * 0.3) * 10
        return round(score, 2)
    
    @staticmethod
    def get_gaussian_weights(n: int) -> list[float]:
        """
        Calcule les poids gaussiens pour une séquence de longueur n.
        Utilisé pour la pondération temporelle ou de similarité.
        """
        if n <= 0:
            return []
        mu = n * 0.4
        sigma = n * 0.8
        x = np.arange(n)
        weights = np.exp(-0.5 * ((x - mu) / sigma)**2)
        return weights.tolist()

    @staticmethod
    def get_ui_score_color_class(score: float) -> str:
        """
        Détermine la classe de couleur UI en fonction d'un score de similarité (0-100).
        Définit les paliers métier de "bonne" ou "mauvaise" réponse.
        """
        if score > 90: return "danger"
        if score > 70: return "warning"
        if score > 40: return "primary"
        return "secondary"
