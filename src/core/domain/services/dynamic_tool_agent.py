import logging
import ast
import traceback
from typing import Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.agent")

class DynamicToolAgent:
    """
    Implémentation d'un Agent capable de créer ses propres outils.
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def build_and_execute_tool(self, api_documentation: str, task: str) -> Dict[str, Any]:
        """
        Demande à l'IA de coder un outil basé sur la doc, puis l'exécute dynamiquement.
        """
        logger.info(f"🛠️ Dynamic Tool Agent: Building tool for task '{task}'...")

        # ... (rest of logic)

        prompt = f"""
        Voici la documentation d'une API :
        {api_documentation}
        
        TA TÂCHE : {task}
        
        MISSION :
        Écris un script Python valide qui accomplit cette tâche en interrogeant l'API.
        Le script DOIT :
        1. Importer `requests`
        2. Définir une fonction `execute_tool()` qui retourne un dictionnaire Python avec les résultats.
        3. Ne faire aucun appel bloquant (input, etc.)
        
        Renvoie UNIQUEMENT le bloc de code Python (sans markdown ni explications).
        """
        
        generated_code = self.inference_engine.generate(prompt, system_prompt="Tu es un Ingénieur Logiciel Senior.")
        
        # Nettoyage rudimentaire du markdown si le modèle l'a tout de même inclus
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
            
        logger.info("💻 Code généré :")
        logger.info(generated_code[:200] + "...")
        
        # Exécution dynamique (Sandbox simulée)
        # ⚠️ WARNING: Use with extreme caution. Local/Trusted LLM only.
        local_scope = {}
        try:
            # Compilation pour vérifier la syntaxe
            ast.parse(generated_code)
            
            # Exécution de la définition de la fonction
            exec(generated_code, globals(), local_scope)
            
            if 'execute_tool' not in local_scope:
                return {"status": "error", "error": "Function 'execute_tool' not defined by the LLM."}
                
            # Exécution de l'outil généré
            logger.info("🚀 Executing dynamic tool...")
            result = local_scope['execute_tool']()
            return {"status": "success", "data": result}
            
        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(f"❌ Dynamic Tool Execution Failed: {e}")
            return {"status": "error", "error": str(e), "traceback": error_msg}
