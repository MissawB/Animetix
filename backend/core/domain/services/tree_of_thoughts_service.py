# -*- coding: utf-8 -*-
"""
Tree-of-Thoughts (ToT) Search Service for Animetix.
Explores multiple reasoning paths and evaluates thought nodes to find the optimal logical consensus.
"""

import logging  # noqa: E402
from typing import Any, Dict, List, TypedDict  # noqa: E402

from core.domain.services.prompt_manager import PromptManager  # noqa: E402
from core.ports.inference_port import InferencePort  # noqa: E402

logger = logging.getLogger("animetix.cognition.tot")


class ThoughtPath(TypedDict):
    """A single reasoning trace explored by the Tree-of-Thoughts search."""

    thought_path: List[str]
    score: float
    text: str
    node_id: str


class TreeOfThoughtsSearchService:
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def solve_with_tree_of_thoughts(
        self, query: str, breadth: int = 3, depth: int = 3
    ) -> Dict[str, Any]:
        """
        Orchestre une exploration Tree-of-Thoughts.
        Chaque étape génère plusieurs branches (breadth) évaluées par un critique.
        """
        logger.info(f"🌳 ToT: Starting Tree-of-Thoughts search for query: '{query}'")

        # Racine de l'arbre
        full_tree = {
            "nodes": [
                {
                    "id": "node_0_0",
                    "label": "Start",
                    "full_text": "Point de départ de la réflexion.",
                    "score": 1.0,
                    "status": "root",
                }
            ],
            "links": [],
        }

        current_paths: List[ThoughtPath] = [
            {"thought_path": [], "score": 1.0, "text": "Start", "node_id": "node_0_0"}
        ]

        for step in range(1, depth + 1):
            logger.info(f"🪜 ToT: Processing Depth Level {step}/{depth}...")
            new_paths: List[ThoughtPath] = []

            for path_idx, path in enumerate(current_paths):
                parent_id = path["node_id"]

                # Génération de branches alternatives (breadth)
                for branch_idx in range(breadth):
                    node_id = f"node_{step}_{path_idx}_{branch_idx}"

                    thought_prompt = (
                        f"Requête : {query}\n"
                        f"Étapes de raisonnement passées : {' -> '.join(path['thought_path'])}\n"
                        f"Génère l'étape suivante (Étape #{step}, Option #{branch_idx + 1}) dans ton raisonnement logique. "
                        f"Sois extrêmement concis (1 phrase)."
                    )

                    try:
                        next_thought = self.inference_engine.generate(
                            prompt=thought_prompt,
                            system_prompt="Tu es un planificateur cognitif d'élite d'arbre de pensées.",
                        ).text.strip()
                    except Exception as e:
                        logger.error(f"Error generating thought branch: {e}")
                        next_thought = (
                            f"Thought option {branch_idx + 1} for step {step}."
                        )

                    # Évaluation par le modèle critique
                    score = self._evaluate_thought_node(
                        query, path["thought_path"], next_thought
                    )

                    # Ajout du nœud au graphe complet (qu'il soit élagué ou non)
                    status = "selected" if score >= 0.5 else "pruned"
                    full_tree["nodes"].append(
                        {
                            "id": node_id,
                            "label": f"E{step} - O{branch_idx + 1}",
                            "full_text": next_thought,
                            "score": score,
                            "status": status,
                        }
                    )
                    full_tree["links"].append({"source": parent_id, "target": node_id})

                    # Seuil d'élagage cognitif (pruning)
                    if score >= 0.5:
                        updated_path = list(path["thought_path"]) + [next_thought]
                        new_paths.append(
                            {
                                "thought_path": updated_path,
                                "score": path["score"] * score,
                                "text": next_thought,
                                "node_id": node_id,
                            }
                        )

            # Si toutes les branches ont été élaguées, on conserve les meilleures du niveau précédent
            if not new_paths:
                logger.warning(
                    "⚠️ ToT: All branches pruned! Falling back to best previous paths."
                )
                break

            # Tri et sélection des meilleures branches (limité à la largeur de recherche breadth)
            new_paths.sort(key=lambda x: x["score"], reverse=True)
            current_paths = new_paths[:breadth]

        # Sélection de la meilleure trace de raisonnement
        best_path: ThoughtPath = (
            current_paths[0]
            if current_paths
            else {
                "thought_path": ["Calcul direct"],
                "score": 0.5,
                "text": "Calcul direct",
                "node_id": "node_0_0",
            }
        )

        # Synthèse finale
        synthesis_prompt = (
            f"Requête initiale : {query}\n"
            f"Trace de pensée sélectionnée par l'arbre sémantique :\n"
            f"{' -> '.join(best_path['thought_path'])}\n\n"
            f"Rédige la réponse finale rigoureuse en français."
        )

        try:
            final_answer = self.inference_engine.generate(
                prompt=synthesis_prompt,
                system_prompt="Tu es le Synthétiseur final d'Animetix.",
            ).text
        except Exception as e:
            logger.error(f"Synthesis failed in ToT: {e}")
            final_answer = "Désolé, la synthèse arborescente a échoué."

        # Ajouter le nœud de synthèse finale
        final_node_id = "node_final"
        full_tree["nodes"].append(
            {
                "id": final_node_id,
                "label": "CONCLUSION",
                "full_text": final_answer,
                "score": 1.0,
                "status": "final",
            }
        )
        full_tree["links"].append(
            {"source": best_path["node_id"], "target": final_node_id}
        )

        return {
            "query": query,
            "best_thought_path": best_path["thought_path"],
            "path_score": best_path["score"],
            "final_answer": final_answer,
            "full_tree": full_tree,
        }

    def solve_with_tree_of_thoughts_stream(
        self, query: str, breadth: int = 3, depth: int = 3
    ):
        """Variante streaming de Tree-of-Thoughts.

        Émet un évènement ``node_created`` par nœud exploré (élagué ou non) puis
        un ``final_answer`` — consommé par l'endpoint SSE du visualiseur ToT.
        """
        yield {
            "type": "node_created",
            "data": {
                "id": "root",
                "parent_id": None,
                "text": "Start",
                "score": 1.0,
                "is_pruned": False,
            },
        }

        current_paths: List[Dict[str, Any]] = [
            {"thought_path": [], "score": 1.0, "text": "Start", "id": "root"}
        ]
        node_counter = 0

        for step in range(1, depth + 1):
            new_paths: List[Dict[str, Any]] = []
            for path in current_paths:
                for branch_idx in range(breadth):
                    node_counter += 1
                    node_id = f"node_{step}_{node_counter}"

                    thought_prompt = (
                        f"Requête : {query}\n"
                        f"Étapes de raisonnement passées : {' -> '.join(path['thought_path'])}\n"
                        f"Génère l'étape suivante (Étape #{step}, Option #{branch_idx + 1}) dans ton raisonnement logique. "
                        f"Sois extrêmement concis (1 phrase)."
                    )

                    try:
                        next_thought = self.inference_engine.generate(
                            prompt=thought_prompt,
                            system_prompt="Tu es un planificateur cognitif d'élite d'arbre de pensées.",
                        ).text.strip()
                    except Exception as e:
                        logger.error(f"Error generating thought branch: {e}")
                        next_thought = (
                            f"Thought option {branch_idx + 1} for step {step}."
                        )

                    score = self._evaluate_thought_node(
                        query, path["thought_path"], next_thought
                    )
                    is_pruned = score < 0.5

                    yield {
                        "type": "node_created",
                        "data": {
                            "id": node_id,
                            "parent_id": path["id"],
                            "text": next_thought,
                            "score": score,
                            "is_pruned": is_pruned,
                        },
                    }

                    if not is_pruned:
                        updated_path = list(path["thought_path"]) + [next_thought]
                        new_paths.append(
                            {
                                "thought_path": updated_path,
                                "score": path["score"] * score,
                                "text": next_thought,
                                "id": node_id,
                            }
                        )

            if not new_paths:
                break

            new_paths.sort(key=lambda x: x["score"], reverse=True)
            current_paths = new_paths[:breadth]

        best_path: Dict[str, Any] = (
            current_paths[0]
            if current_paths
            else {"thought_path": ["Calcul direct"], "score": 0.5}
        )

        synthesis_prompt = (
            f"Requête initiale : {query}\n"
            f"Trace de pensée sélectionnée par l'arbre sémantique :\n"
            f"{' -> '.join(best_path['thought_path'])}\n\n"
            f"Rédige la réponse finale rigoureuse en français."
        )

        try:
            final_answer = self.inference_engine.generate(
                prompt=synthesis_prompt,
                system_prompt="Tu es le Synthétiseur final d'Animetix.",
            ).text
        except Exception as e:
            logger.error(f"Synthesis failed in ToT: {e}")
            final_answer = "Désolé, la synthèse arborescente a échoué."

        yield {"type": "final_answer", "data": {"text": final_answer}}

    def _evaluate_thought_node(
        self, query: str, history: List[str], next_thought: str
    ) -> float:
        """
        Modèle critique local attribuant une note de pertinence sémantique de 0.0 à 1.0.
        """
        critic_prompt = (
            f"Requête : {query}\n"
            f"Historique de pensée : {' -> '.join(history)}\n"
            f"Nouvelle proposition : {next_thought}\n\n"
            f"Attribue une note de pertinence STRICTEMENT sous la forme d'un nombre flottant entre 0.0 et 1.0 (ex: 0.85). "
            f"Ne renvoie rien d'autre que le nombre."
        )

        try:
            score_text = self.inference_engine.generate(
                prompt=critic_prompt,
                system_prompt="Tu es le Critique logique d'arbre de pensées. Réponds uniquement par un chiffre.",
            ).text.strip()
            # Nettoyage et conversion
            import re  # noqa: E402

            match = re.search(r"\d+\.\d+", score_text)
            if match:
                return min(1.0, max(0.0, float(match.group(0))))
            return 0.8  # note de repli par défaut
        except Exception:
            logger.warning(
                "⚠️ Logic Critic evaluation failed. Falling back to default score 0.7.",
                exc_info=True,
            )
            return 0.7
