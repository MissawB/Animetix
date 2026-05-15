import math
import random
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
from .akinetix.question_formatter import QuestionFormatter

logger = logging.getLogger('animetix')

class ClassicalAkinetixService:
    """
    Moteur algorithmique d'Akinetix.
    Gère les probabilités (Bayes) et le choix des questions (Entropie/Information Gain).
    """
    def __init__(self, 
                 catalog_db: List[Dict], 
                 fine_attributes: Optional[Dict] = None,
                 probs: Optional[List[float]] = None, 
                 asked_attributes: Optional[List[str]] = None,
                 formatter: Optional[QuestionFormatter] = None):
        
        self.catalog = catalog_db
        self.fine_attributes = fine_attributes or {}
        self.formatter = formatter or QuestionFormatter()
        
        # Filtrage des items ayant au moins un attribut exploitable
        self.items = [item for item in catalog_db if self._has_attributes(item)]
        self.attributes = self._extract_all_attributes(self.items)
        self.n_items = len(self.items)

        if probs is not None and len(probs) == self.n_items:
            self.probs = np.array(probs)
        else:
            self.reset()
            
        self.asked_attributes = set(asked_attributes) if asked_attributes else set()

    def _has_attributes(self, item: Dict) -> bool:
        """Vérifie si l'item possède des données pour être distingué."""
        char_id = str(item.get('id'))
        if char_id in self.fine_attributes:
            return True
        
        return any([
            item.get('genres'), 
            item.get('micro_tags'), 
            item.get('studios'),
            item.get('metadata', {}).get('themes') if isinstance(item.get('metadata'), dict) else False
        ])

    def _extract_all_attributes(self, db: List[Dict]) -> List[str]:
        """Extrait la liste unique de tous les attributs disponibles dans le pool."""
        attrs = set()
        for item in db:
            char_id = str(item.get('id'))
            # 1. Attributs fins (NLP)
            if char_id in self.fine_attributes:
                for k in self.fine_attributes[char_id].keys():
                    attrs.add(f"fine:{k}")
            
            # 2. Attributs classiques
            if item.get('genres'):
                attrs.update([f"genre:{g}" for g in item.get('genres')])
            if item.get('micro_tags'):
                attrs.update([f"tag:{t}" for t in item.get('micro_tags')])
            if item.get('studios'):
                attrs.update([f"studio:{s}" for s in item.get('studios')])
                
            meta = item.get('metadata', {})
            if isinstance(meta, dict) and meta.get('themes'):
                attrs.update([f"theme:{t}" for t in meta.get('themes')])
                
        return sorted(list(attrs))

    def get_probabilities(self) -> Dict[str, float]:
        """Retourne le mapping Titre -> Probabilité."""
        return { (item.get('title') or item.get('name', 'Inconnu')): prob for item, prob in zip(self.items, self.probs) }

    def reset(self):
        """Réinitialise l'état du jeu."""
        self.n_items = len(self.items)
        if self.n_items == 0:
            self.probs = np.array([])
            return
            
        # Distribution uniforme initiale : P(C_i) = 1/N
        self.probs = np.full(self.n_items, 1.0 / self.n_items)
        self.asked_attributes = set()

    def update_probabilities(self, attribute: str, answer: str):
        """Met à jour les probabilités selon la réponse (Théorème de Bayes)."""
        if self.n_items == 0: return

        # Modèle de vraisemblance (Likelihood)
        # (P(Réponse|Attribut présent), P(Réponse|Attribut absent))
        likelihoods = {
            'yes': (0.9, 0.1),
            'no': (0.1, 0.9),
            'dont_know': (0.5, 0.5),
            'probably': (0.75, 0.25),
            'probably_not': (0.25, 0.75)
        }
        
        p_a_given_h, p_a_given_not_h = likelihoods.get(answer, (0.5, 0.5))
        
        new_probs = np.zeros(self.n_items)
        for i, item in enumerate(self.items):
            has_attr = self._check_attribute_instance(item, attribute)
            p_a_given_ci = p_a_given_h if has_attr else p_a_given_not_h
            # Bayes: Posterior ~ Likelihood * Prior
            new_probs[i] = self.probs[i] * p_a_given_ci
            
        # Normalisation
        total = np.sum(new_probs)
        if total > 1e-9:
            self.probs = new_probs / total
        else:
            self.reset() # Sécurité si les probas tombent à zéro

        self.asked_attributes.add(attribute)

    def _check_attribute_instance(self, item: Dict, attribute: str) -> bool:
        """Vérifie si un item spécifique possède l'attribut donné."""
        if ':' not in attribute: return False
        attr_type, attr_val = attribute.split(':', 1)
        
        if attr_type == 'fine':
            char_id = str(item.get('id'))
            return self.fine_attributes.get(char_id, {}).get(attr_val, False)
            
        if attr_type == 'genre': return attr_val in (item.get('genres') or [])
        if attr_type == 'tag': return attr_val in (item.get('micro_tags') or [])
        if attr_type == 'studio': return attr_val in (item.get('studios') or [])
        if attr_type == 'theme':
            meta = item.get('metadata', {})
            return attr_val in (meta.get('themes') or []) if isinstance(meta, dict) else False
        return False

    def propose_next_question(self) -> Optional[str]:
        """Sélectionne la question maximisant le gain d'information (Entropie)."""
        if self.n_items == 0: return None
        
        candidates = [a for a in self.attributes if a not in self.asked_attributes]
        if not candidates: return None
        
        # Optimisation : Si trop de candidats, on échantillonne
        if len(candidates) > 150:
            fines = [c for c in candidates if c.startswith('fine:')]
            generals = [c for c in candidates if not c.startswith('fine:')]
            candidates = random.sample(fines, min(len(fines), 100)) + random.sample(generals, min(len(generals), 50))
            
        best_attr = None
        best_diff = 1.0 # On cherche p_yes le plus proche de 0.5
            
        for attr in candidates:
            # P(Yes) = Σ P(C_i) pour tous les items ayant l'attribut
            p_yes = sum(self.probs[i] for i, item in enumerate(self.items) if self._check_attribute_instance(item, attr))
            
            # Une question parfaite divise le pool en deux (p_yes = 0.5)
            diff = abs(p_yes - 0.5)
            if diff < best_diff:
                best_diff = diff
                best_attr = attr
                
        return best_attr

    def format_question(self, attribute: str) -> str:
        """Délègue le formatage au QuestionFormatter."""
        return self.formatter.format(attribute)

    def get_best_guess(self) -> Tuple[str, float]:
        """Retourne le candidat le plus probable actuellement."""
        if self.probs is None or self.probs.size == 0:
            return "Inconnu", 0.0
        idx = np.argmax(self.probs)
        item = self.items[idx]
        title = item.get('title') or item.get('name', 'Inconnu')
        return title, self.probs[idx]
