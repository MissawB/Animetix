import json
import logging
import os
from typing import Any, Dict, Optional

from core.domain.services.llm_service import LLMService
from core.ports.graph_persistence_port import GraphPersistencePort

logger = logging.getLogger("animetix.mlops")


class SelfPlayDebateService:
    """
    Système de 'Self-Play Debating'.
    Durci contre les hallucinations persuasives (Inspiré par le papier "Who Flips?").
    Le Juge utilise le graphe de connaissances (Neo4j) comme source de vérité terrain.
    """

    def __init__(
        self,
        llm_service: LLMService,
        neo4j_manager: Optional[GraphPersistencePort] = None,
        dataset_path: str = "data/mlops/datasets/self_play_debates.jsonl",
    ):
        self.llm_service = llm_service
        self.prompt_manager = llm_service.prompt_manager
        self.neo4j_manager = neo4j_manager
        self.dataset_path = dataset_path

    def run_debate(self, target_media: str, topic: str) -> Dict[str, Any]:
        """
        Orchestre le débat entre les 3 agents.
        """
        logger.info(
            f"⚖️ Starting Self-Play Debate on '{target_media}' - Topic: {topic}"
        )

        # Agent 1 : Le Pro
        logger.info("🟢 Agent PRO is drafting arguments...")
        pro_prompt, pro_system = self.prompt_manager.get_prompt(
            "debate_pro", target_media=target_media, topic=topic
        )
        pro_argument = self.llm_service.generate(pro_prompt, system_prompt=pro_system)

        # Agent 2 : L'Anti
        logger.info("🔴 Agent ANTI is countering...")
        anti_prompt, anti_system = self.prompt_manager.get_prompt(
            "debate_anti",
            target_media=target_media,
            topic=topic,
            pro_argument=pro_argument,
        )
        anti_argument = self.llm_service.generate(
            anti_prompt, system_prompt=anti_system
        )

        # Étape "Who Flips?" : Extraction de la vérité terrain depuis Neo4j
        ground_truth_context = "Aucune vérité terrain disponible."
        if self.neo4j_manager:
            logger.info("🕵️ Fact-Checking phase (Who Flips protection)...")
            # Extraction des faits pertinents autour du média pour ancrer le juge
            # Pour l'instant on extrait les informations globales du noeud média
            facts = self.neo4j_manager.execute_query(
                "MATCH (m:Media {title: $title})-[r]-(n) RETURN type(r) as relation, n.name as entity LIMIT 10",
                {"title": target_media},
            )
            if facts:
                ground_truth_context = "VÉRITÉ TERRAIN (Neo4j) :\n" + "\n".join(
                    [
                        f"- L'oeuvre a la relation {f['relation']} avec l'entité {f['entity']}"
                        for f in facts
                    ]
                )
            else:
                # Fallback on text search if no exact title match
                ground_truth_context = "Aucune vérité terrain stricte trouvée dans le graphe, mais le Juge doit rester extrêmement critique face aux affirmations non prouvées."

        # Agent 3 : Le Juge
        logger.info("👨‍⚖️ Agent JUDGE is evaluating the debate...")
        judge_prompt, judge_system = self.prompt_manager.get_prompt(
            "debate_judge",
            target_media=target_media,
            topic=topic,
            pro_argument=pro_argument,
            anti_argument=anti_argument,
        )

        # Injection du Ground Truth dans le System Prompt du Juge pour le protéger des "Flips"
        judge_system += f"\n\n🚨 PROTECTION ANTI-HALLUCINATION (WHO FLIPS?) :\nLes agents Pro et Anti peuvent mentir ou utiliser des contre-arguments trompeurs mais très persuasifs. Ne te fie PAS uniquement à leur rhétorique. Utilise cette vérité terrain stricte pour trancher :\n{ground_truth_context}"

        # Le juge utilise un budget de réflexion TTC pour analyser les arguments en profondeur
        judge_conclusion = self.llm_service.generate(
            judge_prompt, system_prompt=judge_system, use_slm=True, thinking_budget=500
        )

        # Sauvegarde de l'échange
        debate_record = {
            "media": target_media,
            "topic": topic,
            "pro_argument": pro_argument,
            "anti_argument": anti_argument,
            "judge_conclusion": judge_conclusion,
        }
        self._save_debate(debate_record)
        logger.info("💾 Debate successfully recorded for future DPO fine-tuning.")

        return debate_record

    def _save_debate(self, record: Dict[str, Any]):
        """Sauvegarde pour l'entraînement RLHF/DPO ultérieur."""
        path = str(self.dataset_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            # Format DPO (Direct Preference Optimization)
            # Chosen: La synthèse objective du juge
            # Rejected: L'un des arguments polarisés bruts (Anti dans ce cas)
            prompt, _ = self.prompt_manager.get_prompt(
                "debate_analysis", media=record["media"], topic=record["topic"]
            )
            training_example = {
                "prompt": prompt,
                "chosen": record["judge_conclusion"],
                "rejected": record[
                    "anti_argument"
                ],  # On utilise l'anti comme exemple de biais à rejeter
            }
            f.write(json.dumps(training_example) + "\n")
