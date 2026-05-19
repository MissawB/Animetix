import os
import json
import logging
from typing import Dict, Any, List
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")

class SelfPlayDebateService:
    """
    Système de 'Self-Play Debating'.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, dataset_path: str = "data/mlops/datasets/self_play_debates.jsonl"):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.dataset_path = dataset_path

    def run_debate(self, target_media: str, topic: str) -> Dict[str, Any]:
        """
        Orchestre le débat entre les 3 agents.
        """
        logger.info(f"⚖️ Starting Self-Play Debate on '{target_media}' - Topic: {topic}")
        
        # Agent 1 : Le Pro
        logger.info("🟢 Agent PRO is drafting arguments...")
        pro_prompt, pro_system = self.prompt_manager.get_prompt(
            "debate_pro",
            target_media=target_media,
            topic=topic
        )
        pro_argument = self.inference_engine.generate(pro_prompt, system_prompt=pro_system)

        # Agent 2 : L'Anti
        logger.info("🔴 Agent ANTI is countering...")
        anti_prompt, anti_system = self.prompt_manager.get_prompt(
            "debate_anti",
            target_media=target_media,
            topic=topic,
            pro_argument=pro_argument
        )
        anti_argument = self.inference_engine.generate(anti_prompt, system_prompt=anti_system)

        # Agent 3 : Le Juge
        logger.info("👨‍⚖️ Agent JUDGE is evaluating the debate...")
        judge_prompt, judge_system = self.prompt_manager.get_prompt(
            "debate_judge",
            target_media=target_media,
            topic=topic,
            pro_argument=pro_argument,
            anti_argument=anti_argument
        )
        judge_conclusion = self.inference_engine.generate(judge_prompt, system_prompt=judge_system)

        # Sauvegarde de l'échange
        debate_record = {
            "media": target_media,
            "topic": topic,
            "pro_argument": pro_argument,
            "anti_argument": anti_argument,
            "judge_conclusion": judge_conclusion
        }
        self._save_debate(debate_record)
        logger.info("💾 Debate successfully recorded for future DPO fine-tuning.")
        
        return debate_record

    def _save_debate(self, record: Dict[str, Any]):
        """Sauvegarde pour l'entraînement RLHF/DPO ultérieur."""
        path = str(self.dataset_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            # Format DPO (Direct Preference Optimization)
            # Chosen: La synthèse objective du juge
            # Rejected: L'un des arguments polarisés bruts (Anti dans ce cas)
            prompt, _ = self.prompt_manager.get_prompt(
                "debate_analysis",
                media=record['media'],
                topic=record['topic']
            )
            training_example = {
                "prompt": prompt,
                "chosen": record["judge_conclusion"],
                "rejected": record["anti_argument"] # On utilise l'anti comme exemple de biais à rejeter
            }
            f.write(json.dumps(training_example) + "\n")
