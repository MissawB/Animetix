import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger('animetix.neuro_symbolic.solver')

class FormalLogicSolver:
    """
    Solveur de logique formelle utilisant Z3 Theorem Prover.
    Garantit la validité mathématique du raisonnement.
    """
    
    def find_intruder(self, items: List[str], properties: Dict[str, Dict[str, bool]]) -> Tuple[Optional[str], str]:
        """
        Identifie l'intrus parmi une liste d'items basée sur des propriétés booléennes.
        L'intrus est celui qui possède une propriété unique que les autres partagent.
        """
        try:
            import z3
        except ImportError:
            logger.error("z3-solver is not installed. Falling back to mocked logic.")
            return self._mock_solver(items, properties)

        solver = z3.Solver()
        
        # Création des variables booléennes pour chaque item (est-il l'intrus ?)
        intruder_vars = {name: z3.Bool(f'is_intruder_{name}') for name in items}
        
        # Contrainte 1 : Il y a exactement 1 seul intrus
        solver.add(z3.Sum([z3.If(var, 1, 0) for var in intruder_vars.values()]) == 1)

        # Contrainte 2 : Définition de l'intrus par rapport aux propriétés
        # Pour chaque propriété, si un item est différent des autres, il PEUT être l'intrus.
        props = list(list(properties.values())[0].keys())
        
        import z3
        for name in items:
            var = intruder_vars[name]
            others = [n for n in items if n != name]
            
            can_be_intruder_expressions = []
            for prop in props:
                val_target = properties[name].get(prop, False)
                vals_others = [properties[other].get(prop, False) for other in others]
                
                # Un item est l'intrus sur cette propriété si TOUS les autres ont la même valeur
                # et que lui a une valeur différente.
                if len(set(vals_others)) == 1 and val_target != vals_others[0]:
                    can_be_intruder_expressions.append(z3.BoolVal(True))
                else:
                    can_be_intruder_expressions.append(z3.BoolVal(False))
            
            # L'item est l'intrus global si au moins une de ces conditions est vraie
            if can_be_intruder_expressions:
                solver.add(var == z3.Or(can_be_intruder_expressions))
            else:
                solver.add(var == False)

        if solver.check() == z3.sat:
            model = solver.model()
            intruder = next((name for name, var in intruder_vars.items() if z3.is_true(model[var])), None)
            
            proof = f"Z3 SAT: {intruder} is the logical outlier. Properties: {properties}"
            return intruder, proof
        
        return None, "Z3 UNSAT: No clear logical intruder found."

    def _mock_solver(self, items: List[str], properties: Dict[str, Dict[str, bool]]) -> Tuple[Optional[str], str]:
        """Fallback dégradé si Z3 est absent."""
        if not items: return None, "No items"
        props = list(list(properties.values())[0].keys())
        
        for name in items:
            others = [n for n in items if n != name]
            for prop in props:
                val_target = properties[name].get(prop)
                vals_others = [properties[other].get(prop) for other in others]
                if len(set(vals_others)) == 1 and val_target != vals_others[0]:
                    return name, f"Mock SAT: {name} differs on '{prop}'"
                    
        return None, "Mock UNSAT"
