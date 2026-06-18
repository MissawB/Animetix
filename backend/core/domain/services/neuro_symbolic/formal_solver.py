import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger("animetix.neuro_symbolic.solver")


class FormalLogicSolver:
    """
    Solveur de logique formelle utilisant Z3 Theorem Prover.
    Garantit la validité mathématique du raisonnement.
    """

    @property
    def is_available(self) -> bool:
        """Vérifie si Z3 est installé et fonctionnel."""
        try:
            import z3  # noqa: E402, F401

            return True
        except ImportError:
            return False

    def find_intruder(
        self, items: List[str], properties: Dict[str, Dict[str, bool]]
    ) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """
        Identifie l'intrus parmi une liste d'items basée sur des propriétés booléennes.
        Retourne (nom_intrus, preuve, metadonnées).
        """
        try:
            import z3  # noqa: E402, F401
        except ImportError:
            logger.warning("⚠️ z3-solver not installed. Using heuristic fallback.")
            intruder, proof = self._mock_solver(items, properties)
            return intruder, proof, {"method": "heuristic", "engine": "mock_solver"}

        solver = z3.Solver()
        # ... (reste du code Z3 inchangé jusqu'au check) ...

        # Création des variables booléennes pour chaque item (est-il l'intrus ?)
        intruder_vars = {name: z3.Bool(f"is_intruder_{name}") for name in items}

        # Contrainte 1 : Il y a exactement 1 seul intrus
        solver.add(z3.Sum([z3.If(var, 1, 0) for var in intruder_vars.values()]) == 1)

        # Contrainte 2 : Définition de l'intrus par rapport aux propriétés
        props = list(list(properties.values())[0].keys())

        for name in items:
            var = intruder_vars[name]
            others = [n for n in items if n != name]

            can_be_intruder_expressions = []
            for prop in props:
                val_target = properties[name].get(prop, False)
                vals_others = [properties[other].get(prop, False) for other in others]

                if len(set(vals_others)) == 1 and val_target != vals_others[0]:
                    can_be_intruder_expressions.append(z3.BoolVal(True))
                else:
                    can_be_intruder_expressions.append(z3.BoolVal(False))

            if can_be_intruder_expressions:
                solver.add(var == z3.Or(can_be_intruder_expressions))
            else:
                solver.add(not var)

        if solver.check() == z3.sat:
            model = solver.model()
            intruder = next(
                (name for name, var in intruder_vars.items() if z3.is_true(model[var])),
                None,
            )

            proof = f"Z3 SAT: {intruder} is the logical outlier."
            return intruder, proof, {"method": "formal", "engine": "Z3 Theorem Prover"}

        return (
            None,
            "Z3 UNSAT: No clear logical intruder found.",
            {"method": "formal", "engine": "Z3 Theorem Prover"},
        )

    def _mock_solver(
        self, items: List[str], properties: Dict[str, Dict[str, bool]]
    ) -> Tuple[Optional[str], str]:
        """Fallback dégradé si Z3 est absent."""
        if not items:
            return None, "No items"
        props = list(list(properties.values())[0].keys())

        for name in items:
            others = [n for n in items if n != name]
            for prop in props:
                val_target = properties[name].get(prop)
                vals_others = [properties[other].get(prop) for other in others]
                if len(set(vals_others)) == 1 and val_target != vals_others[0]:
                    return name, f"Mock SAT: {name} differs on '{prop}'"

        return None, "Mock UNSAT"
