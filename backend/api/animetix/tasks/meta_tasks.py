# -*- coding: utf-8 -*-
"""
Meta-AI Celery Tasks for Animetix.
Automates prompt optimization and cognitive self-correction using DSPy.
"""

from animetix.tasks_registry import register_task  # noqa: E402
from animetix_project.logging_config import get_logger  # noqa: E402

from ..containers import get_container  # noqa: E402

logger = get_logger("animetix." + __name__)


@register_task("weekly_prompt_optimization")
def weekly_prompt_optimization():
    """
    Tâche hebdomadaire qui optimise les prompts systèmes en fonction des retours négatifs.
    """
    logger.info("🧬 Starting Weekly DSPy Prompt Optimization...")
    container = get_container()

    dspy_optimizer = container.core.dspy_prompt_optimizer()
    dpo_loop = container.core.dpo_feedback_loop()
    prompt_manager = container.infrastructure.prompt_manager()

    # 1. Identifier les prompts les plus "critiqués"
    rejected_feedbacks = dpo_loop.get_rejected_for_curation(limit=50)

    if not rejected_feedbacks:
        logger.info("✅ No negative feedback to optimize. Skipping.")
        return "NO_FEEDBACK"

    # 2. On choisit une clé de prompt à optimiser (ex: 'advanced_rag_generate')
    # Pour la démo, on optimise le prompt de base
    prompt_key = "advanced_rag_generate"
    _, current_template = prompt_manager.get_prompt(
        prompt_key, context="{context}", query="{query}"
    )

    # 3. Création d'un dataset de test à partir des feedbacks négatifs
    test_dataset = []
    for fb in rejected_feedbacks:
        test_dataset.append(
            {
                "query": fb.get("query", ""),
                "expected": "Une réponse plus précise et fidèle au contexte.",  # Placeholder pour l'attendu
            }
        )

    # 4. Lancer l'optimisation DSPy
    logger.info(f"🔬 Optimizing prompt: {prompt_key}")
    best_template, best_score = dspy_optimizer.evaluate_and_select_best(
        current_template, test_dataset
    )

    # 5. Mettre à jour si amélioration
    if best_template != current_template:
        logger.info(
            f"🏆 Improvement found! New score: {best_score:.2f}. Updating PromptManager."
        )
        prompt_manager.update_system_prompt(prompt_key, best_template)
        return f"OPTIMIZED_{prompt_key}"

    return "NO_IMPROVEMENT"


@register_task("scheduled_dpo_optimization")
def scheduled_dpo_optimization():
    """
    Tâche périodique pour optimiser les prompts à partir des feedbacks négatifs accumulés.
    """
    from animetix.models import AIFeedback  # noqa: E402
    from django.core.cache import cache  # noqa: E402
    from django.db.models import Count  # noqa: E402

    lock_id = "scheduled_dpo_optimization_lock"
    if not cache.add(lock_id, "true", 3600):
        logger.warning("🤖 [DPO Task] Already running. Skipping.")
        return "Task already running."

    try:
        container = get_container()
        dpo_loop = container.core.dpo_feedback_loop()
        prompt_manager = container.infrastructure.prompt_manager()

        logger.info("🤖 [DPO Task] Starting automated prompt optimization cycle...")

        MIN_REJECTED_THRESHOLD = 5
        stats = (
            AIFeedback.objects.filter(is_positive=False)
            .values("feedback_type")
            .annotate(rejected_count=Count("id"))
            .filter(rejected_count__gte=MIN_REJECTED_THRESHOLD)
        )

        optimized_categories = []
        for stat in stats:
            prompt_key = stat["feedback_type"]
            if (
                hasattr(prompt_manager, "prompts")
                and prompt_key in prompt_manager.prompts
            ):
                logger.info(
                    f"✨ [DPO Task] Optimizing prompt '{prompt_key}' (Rejected count: {stat['rejected_count']})"
                )
                try:
                    new_prompt = dpo_loop.optimize_prompt_from_feedback(
                        prompt_key, limit=50
                    )
                    if new_prompt:
                        logger.info(
                            f"✅ [DPO Task] Success: Prompt '{prompt_key}' updated."
                        )
                        optimized_categories.append(prompt_key)
                except Exception as e:
                    logger.error(f"❌ [DPO Task] Error optimizing '{prompt_key}': {e}")

        if not optimized_categories:
            return "No prompts needed optimization today."

        return f"Optimization cycle complete. Categories updated: {', '.join(optimized_categories)}"
    finally:
        cache.delete(lock_id)
