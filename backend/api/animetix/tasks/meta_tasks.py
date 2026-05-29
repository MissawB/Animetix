# -*- coding: utf-8 -*-
"""
Meta-AI Celery Tasks for Animetix.
Automates prompt optimization and cognitive self-correction using DSPy.
"""

from animetix_project.logging_config import get_logger
from celery import shared_task
from ..containers import get_container

logger = get_logger('animetix.' + __name__)

@shared_task(name="animetix.meta.optimize_prompts")
def weekly_prompt_optimization():
    """
    Tâche hebdomadaire qui optimise les prompts systèmes en fonction des retours négatifs.
    """
    logger.info("🧬 Starting Weekly DSPy Prompt Optimization...")
    container = get_container()
    
    dspy_optimizer = container.dspy_prompt_optimizer()
    dpo_loop = container.dpo_feedback_loop()
    prompt_manager = container.prompt_manager()
    
    # 1. Identifier les prompts les plus "critiqués"
    rejected_feedbacks = dpo_loop.get_rejected_for_curation(limit=50)
    
    if not rejected_feedbacks:
        logger.info("✅ No negative feedback to optimize. Skipping.")
        return "NO_FEEDBACK"
        
    # 2. On choisit une clé de prompt à optimiser (ex: 'advanced_rag_generate')
    # Pour la démo, on optimise le prompt de base
    prompt_key = "advanced_rag_generate"
    _, current_template = prompt_manager.get_prompt(prompt_key, context="{context}", query="{query}")
    
    # 3. Création d'un dataset de test à partir des feedbacks négatifs
    test_dataset = []
    for fb in rejected_feedbacks:
        test_dataset.append({
            "query": fb.get('query', ''),
            "expected": "Une réponse plus précise et fidèle au contexte." # Placeholder pour l'attendu
        })
        
    # 4. Lancer l'optimisation DSPy
    logger.info(f"🔬 Optimizing prompt: {prompt_key}")
    best_template, best_score = dspy_optimizer.evaluate_and_select_best(current_template, test_dataset)
    
    # 5. Mettre à jour si amélioration
    if best_template != current_template:
        logger.info(f"🏆 Improvement found! New score: {best_score:.2f}. Updating PromptManager.")
        prompt_manager.update_system_prompt(prompt_key, best_template)
        return f"OPTIMIZED_{prompt_key}"
        
    return "NO_IMPROVEMENT"
