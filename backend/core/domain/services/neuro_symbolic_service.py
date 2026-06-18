import logging
from typing import Tuple, Optional, Dict, Any
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager
from .neuro_symbolic.formal_solver import FormalLogicSolver
from .neuro_symbolic.semantic_oracle import SemanticOracle

logger = logging.getLogger("animetix.neuro_symbolic")


class NeuroSymbolicService:
    """
    Service de Raisonnement Hybride (Neuro-Symbolique).
    Orchestre l'Oracle (LLM) et le Solveur Formel (Z3).
    """

    def __init__(
        self,
        inference_engine: InferencePort,
        prompt_manager: PromptManager,
        solver: Optional[FormalLogicSolver] = None,
    ):
        self.oracle = SemanticOracle(inference_engine, prompt_manager)
        self.solver = solver or FormalLogicSolver()

    def solve_paradox(
        self, media_type: str, item_a: str, item_b: str, item_c: str
    ) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """
        Résout le Paradoxe :
        1. Extraction des faits sémantiques (Oracle/LLM).
        2. Preuve logique de l'intrus (Solver/Z3).
        3. Explication narrative (Oracle/LLM).
        """
        items = [item_a, item_b, item_c]

        # 1. Extraction via LLM
        logger.info(f"🧠 Step 1: Semantic Fact Extraction for {items}")
        properties = self.oracle.extract_properties(media_type, items)
        if not properties:
            return (
                None,
                "L'Oracle n'a pas pu extraire de faits discriminants.",
                {"confidence": "low", "reason": "No properties extracted"},
            )

        # 2. Résolution via Logique Formelle
        logger.info("⚙️ Step 2: Formal Logic Resolution (Z3)")
        intruder, proof, meta = self.solver.find_intruder(items, properties)

        if not intruder:
            return (
                None,
                "Aucun intrus n'a pu être identifié de manière rigoureuse.",
                meta,
            )

        # 3. Vulgarisation via LLM
        logger.info(f"🗣️ Step 3: Natural Language Explanation for {intruder}")
        explanation = self.oracle.explain_proof(intruder, proof)

        return intruder, explanation, meta
