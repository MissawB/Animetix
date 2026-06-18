# -*- coding: utf-8 -*-
"""
Neuro-Symbolic User Profiler using Z3 Solver for Animetix.
Deduces formal logical preference rules from user positive/negative feedbacks.
"""

import logging  # noqa: E402
from typing import Any, Dict, List  # noqa: E402

logger = logging.getLogger("animetix.neurosymbolic.profiler")


class NeuroSymbolicUserProfiler:
    def __init__(self, feedback_adapter=None):
        self.feedback_adapter = feedback_adapter
        self.rules: List[str] = []

    def deduce_preference_rules(
        self, user_feedbacks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Analyse les retours utilisateurs (input_context, is_positive) pour en déduire
        des contraintes logiques SAT résolues par Z3.
        """
        logger.info("🧩 Neuro-Symbolic: Analyzing feedback constraints...")

        if not user_feedbacks:
            return ["Default: User likes standard Nekketsu"]

        # Extraction de caractéristiques (ex: Shonen, Seinen, Épisodes courts, Violence)
        # Chaque feedback représente un état de fait
        facts = []
        for fb in user_feedbacks:
            if fb.get("is_ignored", False):
                continue

            ctx = fb.get("input_context", "").lower()
            is_pos = fb.get("is_positive", True)
            weight = fb.get("weight", 1.0)

            # Vecteur de traits booléens
            has_shonen = "shonen" in ctx or "nekketsu" in ctx
            has_seinen = "seinen" in ctx or "sombre" in ctx
            has_violence = "violence" in ctx or "sanglant" in ctx
            has_short = "court" in ctx or "12 ep" in ctx

            facts.append(
                {
                    "shonen": has_shonen,
                    "seinen": has_seinen,
                    "violence": has_violence,
                    "short": has_short,
                    "satisfied": is_pos,
                    "weight": weight,
                }
            )

        # --- Résolution Formelle SAT avec Z3 ---
        try:
            import z3  # noqa: E402

            # Variables de propositions logiques
            shonen = z3.Bool("shonen")
            seinen = z3.Bool("seinen")
            violence = z3.Bool("violence")
            short = z3.Bool("short")

            solver = z3.Solver()

            # Traduction des retours en assertions logiques
            for idx, fact in enumerate(facts):
                # Formule représentant le cas utilisateur
                formula = z3.And(
                    shonen == fact["shonen"],
                    seinen == fact["seinen"],
                    violence == fact["violence"],
                    short == fact["short"],
                )
                # Si le feedback est positif, l'état doit être SAT. S'il est négatif, l'état est contraint négativement.
                if fact["satisfied"]:
                    solver.add(formula)
                else:
                    solver.add(z3.Not(formula))

            # Résolution
            if solver.check() == z3.sat:
                model = solver.model()
                rules = []
                for decl in model.decls():
                    val = model[decl]
                    rules.append(f"{decl.name()} == {val}")
                self.rules = rules
                logger.info(
                    f"🧩 Neuro-Symbolic Z3 Solver: Deduced {len(rules)} formal preference bounds."
                )
                return rules
            else:
                logger.warning(
                    "🧩 Z3 UNSAT: Preference constraints are contradictory. Softening logic bounds."
                )

        except ImportError:
            logger.warning(
                "⚠️ Z3 logic solver package not pre-installed. Falling back to pure Python symbolic engine."
            )

        # --- Moteur de repli Symbolique Pure Python ---
        rules = []
        likes_shonen = any(f["shonen"] and f["satisfied"] for f in facts)
        likes_seinen = any(f["seinen"] and f["satisfied"] for f in facts)
        dislikes_violence = any(f["violence"] and not f["satisfied"] for f in facts)

        if likes_seinen:
            rules.append("Prefer == Seinen")
        if likes_shonen:
            rules.append("Prefer == Shonen")
        if dislikes_violence:
            rules.append("Avoid == Violence")

        self.rules = rules
        logger.info(f"🧩 Symbolic Rule Engine: Deduced {len(rules)} rules.")
        return rules
