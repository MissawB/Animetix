# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict

from core.ports.gold_dataset_port import GoldDatasetPort
from core.ports.inference_port import InferencePort

from .guardrail_service import GuardrailService
from .xai_service import XaiDiagnosticService

logger = logging.getLogger("animetix.validation.gate")


class SyntheticValidationService:
    """
    Universal HITL Gate: Centralizes the validation of all synthetic data
    before staging for human moderation.
    Implements cross-validation to prevent Model Collapse.
    """

    def __init__(
        self,
        inference_engine: InferencePort,
        gold_dataset_port: GoldDatasetPort,
        guardrail_service: GuardrailService,
        xai_service: XaiDiagnosticService,
    ):
        self.inference_engine = inference_engine
        self.gold_dataset_port = gold_dataset_port
        self.guardrail_service = guardrail_service
        self.xai_service = xai_service

    def validate_and_stage(
        self,
        entry_type: str,
        context: str,
        instruction: str,
        response: str,
        metadata: Dict[str, Any] = None,
    ) -> int:
        """
        Runs systematic AI cross-validation and stages the entry for HITL review.
        """
        logger.info(
            f"🚦 [HITL Gate] Validating {entry_type} entry: '{instruction[:50]}...'"
        )

        # 1. Safety & Factual Guardrail Check
        safety_report = self.guardrail_service.validate_output(
            response, context=context, query=instruction
        )
        is_safe = safety_report.get("is_safe", True)
        safety_reason = safety_report.get("reason", "")

        # 2. XAI Confidence Scoring
        xai_report = self.xai_service.measure_confidence(instruction, response)
        confidence_score = xai_report.get("confidence_score", 0.0)

        # 3. AI Cross-Critique (Self or Third-Party)
        ai_critique, validation_score = self._run_ai_critique(
            context, instruction, response
        )

        # 4. Final aggregation of risks for the human moderator
        if not is_safe:
            ai_critique = f"🚨 SAFETY RISK: {safety_reason}\n\n" + ai_critique
            validation_score = min(validation_score, 0.2)

        # 5. Staging for HITL with Data Scrubbing
        from core.utils.scrubbing import scrub_sensitive_data  # noqa: E402

        entry_id = self.gold_dataset_port.save_synthetic_entry(
            entry_type=entry_type,
            context=scrub_sensitive_data(context),
            instruction=scrub_sensitive_data(instruction),
            response=scrub_sensitive_data(response),
            metadata=scrub_sensitive_data(metadata),
            ai_validation_score=validation_score,
            ai_critique=scrub_sensitive_data(ai_critique),
            confidence_score=confidence_score,
            is_safe=is_safe,
        )

        logger.info(
            f"✅ [HITL Gate] Entry {entry_id} staged with AI Score: {validation_score:.2f} (Confidence: {confidence_score:.2f})"
        )
        return entry_id

    def _run_ai_critique(
        self, context: str, instruction: str, response: str
    ) -> (str, float):
        """
        Forces a model to critique the generated content for coherence,
        fidelity to context, and quality.
        """
        critique_prompt = f"""
Tu es un Auditeur Qualité IA expert. Ta mission est de critiquer sévèrement la réponse suivante par rapport à son contexte et son instruction.

CONTEXTE:
{context}

INSTRUCTION:
{instruction}

RÉPONSE À ÉVALUER:
{response}

TACHE:
1. Analyse si la réponse invente des faits non présents dans le contexte (hallucination).
2. Vérifie si le ton est approprié pour Animetix.
3. Donne un score de QUALITÉ GLOBALE entre 0.0 et 1.0.

Réponds au format JSON suivant :
{{
  "critique": "Ton analyse détaillée ici",
  "score": 0.85
}}
"""
        try:
            critique_res = self.inference_engine.generate(
                critique_prompt, system_prompt="Tu es l'Auditeur Suprême d'Animetix."
            )
            import json  # noqa: E402
            import re  # noqa: E402

            text = critique_res.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()

            # Basic cleanup
            text = text.strip()
            if not text.startswith("{"):
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    text = match.group(0)

            data = json.loads(text)
            return data.get("critique", "No critique provided."), float(
                data.get("score", 0.5)
            )
        except Exception as e:
            logger.warning(f"⚠️ AI Critique failed: {e}")
            return f"Critique engine failure: {str(e)}", 0.5
