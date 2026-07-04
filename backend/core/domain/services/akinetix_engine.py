import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..entities.akinetix import AkinetixGameState, AkinetixQuestion
from .akinetix.question_formatter import QuestionFormatter, is_valid_micro_tag
from .akinetix_rl_env import AkinetixRLEnvironment
from .catalog_service import CatalogService

logger = logging.getLogger("animetix.akinetix.engine")


class AkinetixEngine:
    """
    Unified Engine for Akinetix game logic.
    Combines Bayesian (Classical) and Reinforcement Learning (RL) strategies.
    """

    # Decision thresholds
    PROBABILITY_THRESHOLD = 0.8
    MIN_STEPS_BEFORE_GUESS = 5
    MAX_STEPS_TOTAL = 25

    # Answer mapping (anything else falls back to "dont_know")
    ANSWER_MAPPING = {
        "OUI": "yes",
        "NON": "no",
        "PROBABLEMENT": "probably",
        "PROBABLEMENT PAS": "probably_not",
        "JE NE SAIS PAS": "dont_know",
        # Backward-compat with the old single "maybe" button.
        "PEUT-ÊTRE": "probably",
    }

    def __init__(
        self,
        catalog_service: CatalogService,
        formatter: Optional[QuestionFormatter] = None,
        cfr_solver: Any = None,
    ):
        self.catalog_service = catalog_service
        self.formatter = formatter or QuestionFormatter()
        self.cfr_solver = cfr_solver

    def get_next_question(
        self, candidates: List[str], game_state: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        Délègue la sélection de la meilleure question au solveur CFR si disponible,
        sinon retourne la première avec une confiance par défaut.
        """
        if self.cfr_solver:
            return self.cfr_solver.solve_best_question(candidates, game_state)

        # Fallback si pas de solveur (heuristique simple)
        return candidates[0] if candidates else "Inconnu", 0.5

    def start_game(
        self, catalog_db: List[Dict], mode: str = "classical"
    ) -> AkinetixGameState:
        """Starts a new game with the chosen mode."""
        logger.info(f"Starting new Akinetix game session (mode: {mode}).")

        if mode == "rl":
            return self._start_rl_game(catalog_db)
        return self._start_classical_game(catalog_db)

    def process_answer(
        self,
        catalog_db: List[Dict],
        state: AkinetixGameState,
        raw_answer: str,
        mode: str = "classical",
    ) -> AkinetixGameState:
        """Processes an answer and moves to the next state."""
        if mode == "rl":
            return self._process_rl_answer(catalog_db, state, raw_answer)
        return self._process_classical_answer(catalog_db, state, raw_answer)

    # --- Classical Strategy Implementation ---

    def _start_classical_game(self, catalog_db: List[Dict]) -> AkinetixGameState:
        fine_attrs = self.catalog_service.get_akinetix_attributes()
        items, attributes = self._prepare_classical_data(catalog_db, fine_attrs)

        n_items = len(items)
        probs = np.full(n_items, 1.0 / n_items) if n_items > 0 else np.array([])

        # Initial question
        next_attr = self._propose_classical_question(items, attributes, probs, set())

        return AkinetixGameState(
            history=[],
            current_q=self.formatter.format(next_attr or ""),
            current_attr=next_attr,
            game_over=False,
            ai_guess=None,
            probs=probs.tolist(),
            asked_attrs=[],
        )

    def _process_classical_answer(
        self, catalog_db: List[Dict], state: AkinetixGameState, raw_answer: str
    ) -> AkinetixGameState:
        answer = self.ANSWER_MAPPING.get(raw_answer.upper(), "dont_know")
        fine_attrs = self.catalog_service.get_akinetix_attributes()
        items, attributes = self._prepare_classical_data(catalog_db, fine_attrs)

        probs = np.array(state.probs)
        asked_attrs = set(state.asked_attrs)

        # The candidate pool is re-derived from the catalog on every answer; if
        # it no longer matches the vector sized at game start (catalog reloaded
        # or difficulty slice lost), restart from uniform instead of crashing.
        if probs.size != len(items):
            logger.warning(
                "Probs/items size mismatch (%d vs %d); resetting to uniform.",
                probs.size,
                len(items),
            )
            probs = np.full(len(items), 1.0 / len(items)) if items else np.array([])

        if state.current_attr:
            probs = self._update_classical_probs(
                items, probs, state.current_attr, answer, fine_attrs
            )
            asked_attrs.add(state.current_attr)

        state.history.append(AkinetixQuestion(q=state.current_q, a=raw_answer))
        state.probs = probs.tolist()
        state.asked_attrs = list(asked_attrs)

        best_title, best_prob = self._get_classical_best_guess(items, probs)
        steps = len(asked_attrs)

        state.confidence = self._compute_confidence(probs, best_prob)

        if (
            best_prob > self.PROBABILITY_THRESHOLD
            and steps >= self.MIN_STEPS_BEFORE_GUESS
        ) or steps >= self.MAX_STEPS_TOTAL:
            state.current_q = f"Est-ce que tu penses à : {best_title} ?"
            state.ai_guess = best_title
            state.game_over = True
            state.confidence = 1.0
        else:
            next_attr = self._propose_classical_question(
                items, attributes, probs, asked_attrs, fine_attrs
            )
            if next_attr:
                state.current_q = self.formatter.format(next_attr)
                state.current_attr = next_attr
            else:
                state.current_q = (
                    f"Je ne sais plus quoi demander... Serait-ce {best_title} ?"
                )
                state.ai_guess = best_title
                state.game_over = True

        return state

    def _prepare_classical_data(
        self, catalog_db: List[Dict], fine_attributes: Dict
    ) -> Tuple[List[Dict], List[str]]:
        items = [
            item for item in catalog_db if self._has_attributes(item, fine_attributes)
        ]
        attrs = set()
        for item in items:
            char_id = str(item.get("id"))
            if char_id in fine_attributes:
                for k in fine_attributes[char_id].keys():
                    attrs.add(f"fine:{k}")
            if item.get("genres"):
                attrs.update([f"genre:{g}" for g in (item.get("genres") or [])])
            for t in self._item_tags(item):
                attrs.add(f"tag:{t}")
            if item.get("studios"):
                attrs.update([f"studio:{s}" for s in (item.get("studios") or [])])
            meta = item.get("metadata", {})
            if isinstance(meta, dict) and meta.get("themes"):
                attrs.update([f"theme:{t}" for t in (meta.get("themes") or [])])
            era = self._item_era(item)
            if era:
                attrs.add(f"era:{era}")
        return items, sorted(list(attrs))

    @staticmethod
    def _item_era(item: Dict) -> Optional[str]:
        """Tranche temporelle d'une œuvre (à partir de ``year``), formulée pour
        une question naturelle. Nouvel axe : « Est-ce sorti dans les années X ? »."""
        year = item.get("year")
        if year is None:
            return None
        try:
            y = int(year)
        except (TypeError, ValueError):
            return None
        if y < 1990:
            return "avant 1990"
        if y < 2000:
            return "dans les années 1990"
        if y < 2010:
            return "dans les années 2000"
        if y < 2020:
            return "dans les années 2010"
        return "dans les années 2020"

    def _item_tags(self, item: Dict) -> List[str]:
        """Tags thématiques valides d'une œuvre.

        Fusionne le champ riche ``tags`` (tags AniList, ~380 valeurs) avec
        ``micro_tags`` et écarte les entrées polluées/erreurs (pipeline de
        tagging lancé sans unité de calcul). Le moteur n'utilisait que
        ``micro_tags``, cassé, d'où des questions de tag quasi inexistantes.
        """
        raw = list(item.get("tags") or []) + list(item.get("micro_tags") or [])
        return [t for t in raw if is_valid_micro_tag(t)]

    def _has_attributes(self, item: Dict, fine_attributes: Dict) -> bool:
        char_id = str(item.get("id"))
        if char_id in fine_attributes:
            return True
        return any(
            [
                item.get("genres"),
                item.get("micro_tags"),
                item.get("studios"),
                (
                    item.get("metadata", {}).get("themes")
                    if isinstance(item.get("metadata"), dict)
                    else False
                ),
            ]
        )

    def _update_classical_probs(
        self,
        items: List[Dict],
        probs: np.ndarray,
        attribute: str,
        answer: str,
        fine_attributes: Dict,
    ) -> np.ndarray:
        if len(items) == 0:
            return probs
        likelihoods = {
            "yes": (0.9, 0.1),
            "no": (0.1, 0.9),
            "dont_know": (0.5, 0.5),
            "probably": (0.75, 0.25),
            "probably_not": (0.25, 0.75),
        }
        p_a_given_h, p_a_given_not_h = likelihoods.get(answer, (0.5, 0.5))
        new_probs = np.zeros(len(items))
        for i, item in enumerate(items):
            has_attr = self._check_attribute_instance(item, attribute, fine_attributes)
            p_a_given_ci = p_a_given_h if has_attr else p_a_given_not_h
            new_probs[i] = probs[i] * p_a_given_ci
        total = np.sum(new_probs)
        return (
            new_probs / total if total > 1e-9 else np.full(len(items), 1.0 / len(items))
        )

    def _item_attribute_set(self, item: Dict, fine_attributes: Dict) -> set:
        """All attribute keys an item satisfies, for O(1) membership lookups."""
        attrs = set()
        for g in item.get("genres") or []:
            attrs.add(f"genre:{g}")
        for t in self._item_tags(item):
            attrs.add(f"tag:{t}")
        for s in item.get("studios") or []:
            attrs.add(f"studio:{s}")
        meta = item.get("metadata", {})
        if isinstance(meta, dict):
            for th in meta.get("themes") or []:
                attrs.add(f"theme:{th}")
        item_fine = fine_attributes.get(str(item.get("id")), {})
        if isinstance(item_fine, dict):
            for k, v in item_fine.items():
                if v:
                    attrs.add(f"fine:{k}")
        era = self._item_era(item)
        if era:
            attrs.add(f"era:{era}")
        return attrs

    def _check_attribute_instance(
        self, item: Dict, attribute: str, fine_attributes: Dict
    ) -> bool:
        if ":" not in attribute:
            return False
        attr_type, attr_val = attribute.split(":", 1)
        if attr_type == "fine":
            return fine_attributes.get(str(item.get("id")), {}).get(attr_val, False)
        if attr_type == "genre":
            return attr_val in (item.get("genres") or [])
        if attr_type == "tag":
            return attr_val in self._item_tags(item)
        if attr_type == "studio":
            return attr_val in (item.get("studios") or [])
        if attr_type == "theme":
            meta = item.get("metadata", {})
            return (
                attr_val in (meta.get("themes") or [])
                if isinstance(meta, dict)
                else False
            )
        if attr_type == "era":
            return self._item_era(item) == attr_val
        return False

    def _propose_classical_question(
        self,
        items: List[Dict],
        attributes: List[str],
        probs: np.ndarray,
        asked_attrs: set,
        fine_attributes: Optional[Dict] = None,
    ) -> Optional[str]:
        candidates = [a for a in attributes if a not in asked_attrs]
        if not candidates:
            return None

        # Inverted index attribute -> item indices, built once. Avoids re-scanning
        # every item (with a per-call split) for each candidate: the previous
        # O(candidates x items) double loop dominated the per-answer latency.
        considered = candidates[:200]  # Limite pour la performance
        considered_set = set(considered)
        attr_to_indices: Dict[str, List[int]] = {}
        for i, item in enumerate(items):
            for attr in self._item_attribute_set(item, fine_attributes or {}):
                if attr in considered_set:
                    attr_to_indices.setdefault(attr, []).append(i)

        # 1. Calcul de l'entropie (gain d'information) pour chaque candidat
        scored_candidates = []
        for attr in considered:
            idx = attr_to_indices.get(attr)
            p_yes = float(probs[idx].sum()) if idx else 0.0
            gain = 1.0 - abs(p_yes - 0.5) * 2  # 1.0 = entropie max, 0.0 = min
            scored_candidates.append((attr, gain))

        # Tri par gain d'information décroissant
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = [x[0] for x in scored_candidates[:10]]

        # 2. Utilisation du solveur CFR pour choisir le chemin optimal parmi les meilleurs
        if self.cfr_solver:
            game_state = {
                "probs": probs.tolist(),
                "asked_attrs": list(asked_attrs),
                "items_count": len(items),
            }
            best_attr, _ = self.get_next_question(top_candidates, game_state)
            return best_attr

        # Fallback classique (le meilleur selon l'entropie pure)
        return top_candidates[0] if top_candidates else None

    def _get_classical_best_guess(
        self, items: List[Dict], probs: np.ndarray
    ) -> Tuple[str, float]:
        if probs.size == 0:
            return "Inconnu", 0.0
        idx = np.argmax(probs)
        item = items[idx]
        title = item.get("title") or item.get("name", "Inconnu")
        return title, probs[idx]

    def _compute_confidence(self, probs: np.ndarray, best_prob: float) -> float:
        """Progression 0..1 « à quel point l'IA est proche de deviner ».

        Combine deux signaux et garde le maximum :
        - l'information acquise (réduction d'entropie de la distribution),
          passée en racine carrée pour que la barre bouge nettement dès les
          premières questions plutôt que de rester collée à 0 ;
        - la confiance du meilleur candidat normalisée par le seuil de décision,
          qui garantit que la barre atteint 100 % au moment où l'IA tranche.
        """
        threshold = self.PROBABILITY_THRESHOLD
        threshold_progress = (
            min(1.0, best_prob / threshold) if threshold > 0 else min(1.0, best_prob)
        )

        reactive = 0.0
        positive = probs[probs > 0]
        n = probs.size
        if positive.size and n > 1:
            entropy = float(-np.sum(positive * np.log(positive)))
            max_entropy = float(np.log(n))
            if max_entropy > 0:
                info_gained = 1.0 - entropy / max_entropy
                reactive = float(np.sqrt(max(0.0, min(1.0, info_gained))))

        return float(min(1.0, max(reactive, threshold_progress)))

    # --- RL Strategy Implementation ---

    def _start_rl_game(self, catalog_db: List[Dict]) -> AkinetixGameState:
        env = AkinetixRLEnvironment(catalog_db)
        # Simulation d'une action initiale (gain d'info max)
        action_idx = self._rl_get_best_action(env)
        next_attr = env.attributes[action_idx]

        return AkinetixGameState(
            history=[],
            current_q=self._rl_format_question(next_attr),
            current_attr=next_attr,
            game_over=False,
            ai_guess=None,
            probs=[],
            asked_attrs=[],
        )

    def _process_rl_answer(
        self, catalog_db: List[Dict], state: AkinetixGameState, raw_answer: str
    ) -> AkinetixGameState:
        # Simplification: l'env RL est stateless ici, on simule le filtrage
        asked_attrs = state.asked_attrs
        if state.current_attr:
            asked_attrs.append(state.current_attr)

        state.history.append(AkinetixQuestion(q=state.current_q, a=raw_answer))
        steps = len(state.history)

        # Reconstruire un env partiel pour la décision
        env = AkinetixRLEnvironment(catalog_db)
        # On réduit le pool de candidats manuellement pour l'heuristique
        filtered_candidates = self._rl_filter_candidates(
            catalog_db, state.history, asked_attrs
        )
        env.active_candidates = filtered_candidates

        pool_size = len(filtered_candidates)

        if pool_size <= 1 or steps >= 20:
            best_match = (
                filtered_candidates[0] if filtered_candidates else catalog_db[0]
            )
            state.current_q = f"L'IA prédictive pense à : {best_match['title']}"
            state.ai_guess = best_match["title"]
            state.game_over = True
        else:
            action_idx = self._rl_get_best_action(env)
            next_attr = env.attributes[action_idx]
            state.current_q = self._rl_format_question(next_attr)
            state.current_attr = next_attr
            state.asked_attrs = asked_attrs

        return state

    def _rl_get_best_action(self, env: AkinetixRLEnvironment) -> int:
        best_action = 0
        max_gain = -1.0
        sample_size = min(20, len(env.attributes))
        indices = np.random.choice(len(env.attributes), sample_size, replace=False)
        for idx in indices:
            gain = self._rl_simulate_info_gain(env, idx)
            if gain > max_gain:
                max_gain = gain
                best_action = idx
        return best_action

    def _rl_simulate_info_gain(
        self, env: AkinetixRLEnvironment, action_idx: int
    ) -> float:
        attr = env.attributes[action_idx]
        attr_type, attr_val = attr.split(":", 1)
        count = sum(
            1
            for item in env.active_candidates
            if self._rl_check_attr(item, attr_type, attr_val)
        )
        ratio = count / len(env.active_candidates) if env.active_candidates else 0
        return 1.0 - abs(0.5 - ratio)

    def _rl_check_attr(self, item, attr_type, attr_val):
        if attr_type == "genre":
            return attr_val in item.get("genres", [])
        if attr_type == "tag":
            return attr_val in item.get("micro_tags", [])
        if attr_type == "studio":
            return attr_val in item.get("studios", [])
        return False

    def _rl_filter_candidates(
        self, db: List[Dict], history: List[Any], asked_attrs: List[str]
    ) -> List[Dict]:
        # Filtrage réel basé sur l'historique des réponses utilisateur
        candidates = db
        for i, question_obj in enumerate(history):
            if i >= len(asked_attrs):
                break
            attr = asked_attrs[i]
            if ":" not in attr:
                continue
            attr_type, attr_val = attr.split(":", 1)
            raw_ans = question_obj.a.upper()

            if raw_ans == "OUI":
                candidates = [
                    c for c in candidates if self._rl_check_attr(c, attr_type, attr_val)
                ]
            elif raw_ans == "NON":
                candidates = [
                    c
                    for c in candidates
                    if not self._rl_check_attr(c, attr_type, attr_val)
                ]

        return candidates if candidates else db[:1]

    def _rl_format_question(self, attribute: str) -> str:
        return self.formatter.format(attribute)
