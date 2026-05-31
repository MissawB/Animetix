import logging
from typing import Dict, Any
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.agent")

class DynamicToolAgent:
    """
    Agent capable of proposing its own tools (EXPOSÉ À DES RISQUES DE SÉCURITÉ).
    NOTE: L'exécution dynamique via exec() a été supprimée pour prévenir les attaques RCE.
    Cet agent ne peut désormais que GÉNÉRER le code du système, pas l'exécuter.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, timeout_seconds: int = 5):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.timeout_seconds = timeout_seconds

    def build_and_execute_tool(self, api_documentation: str, task: str) -> Dict[str, Any]:
        """
        Génère le code d'un outil mais REFUSE de l'exécuter pour des raisons de sécurité.
        """
        logger.info(f"🛠️ Dynamic Tool Agent: Proposing tool for task '{task}'...")

        prompt, system = self.prompt_manager.get_prompt(
            "dynamic_tool_builder",
            api_documentation=api_documentation,
            task=task
        )

        generated_code = self.inference_engine.generate(prompt, system_prompt=system)

        logger.info("💻 Code proposed by AI (execution disabled for security).")
        
        return {
            "status": "security_disabled",
            "message": "L'exécution dynamique de code est désactivée sur ce serveur pour prévenir les failles RCE.",
            "proposed_code": generated_code
        }
