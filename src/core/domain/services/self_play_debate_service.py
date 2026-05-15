import os
import json
import logging
from typing import Dict, Any, List
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.mlops")

class SelfPlayDebateService:
    """
    Système de 'Self-Play Debating'.
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine
        self.dataset_path = "data/mlops/datasets/self_play_debates.jsonl"

    def run_debate(self, target_media: str, topic: str) -> Dict[str, Any]:
        """
        Orchestre le débat entre les 3 agents.
        """
        logger.info(f"⚖️ Starting Self-Play Debate on '{target_media}' - Topic: {topic}")
        
        # Agent 1 : Le Pro
        logger.info("🟢 Agent PRO is drafting arguments...")
        pro_prompt = f"Tu es un critique expert qui ADORE {target_media}. Défends la thèse suivante : '{topic}'. Sois précis, cite des scènes ou thèmes exacts."
        pro_argument = self.inference_engine.generate(pro_prompt, system_prompt="Tu es l'Avocat de la Défense.")

        # Agent 2 : L'Anti
        logger.info("🔴 Agent ANTI is countering...")
        anti_prompt = f"""
        Tu es un critique expert très sévère envers {target_media}. 
        Voici l'argumentaire de la défense concernant le sujet '{topic}' :
        {pro_argument}
        
        Détruis cet argumentaire. Trouve des failles, pointe les incohérences ou les faiblesses de l'œuvre sur ce sujet précis.
        """
        anti_argument = self.inference_engine.generate(anti_prompt, system_prompt="Tu es le Procureur.")

        # Agent 3 : Le Juge
        logger.info("👨‍⚖️ Agent JUDGE is evaluating the debate...")
        judge_prompt = f"""
        En tant que juge impartial, analyse ce débat sur l'œuvre {target_media} (Sujet : {topic}).
        
        ARGUMENT PRO :
        {pro_argument}
        
        ARGUMENT ANTI :
        {anti_argument}
        
        SYNTHÈSE EXIGÉE :
        Qui a les meilleurs arguments factuels ? Génère une conclusion finale nuancée 
        qui représente la "vérité terrain" objective sur cette œuvre.
        """
        judge_conclusion = self.inference_engine.generate(judge_prompt, system_prompt="Tu es le Juge Suprême. Ton analyse est purement objective et logique.")

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
            prompt = f"Analyse les forces et faiblesses de {record['media']} concernant le sujet '{record['topic']}'."
            training_example = {
                "prompt": prompt,
                "chosen": record["judge_conclusion"],
                "rejected": record["anti_argument"] # On utilise l'anti comme exemple de biais à rejeter
            }
            f.write(json.dumps(training_example) + "\n")
