import os
import yaml
import logging
import json
from typing import Dict, Any, Optional, List
from filelock import FileLock, Timeout

logger = logging.getLogger("animetix.prompts")

class PromptManager:
    """
    Manages externalized prompts from YAML files and dynamic few-shot examples for self-correction.
    """
    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, Any] = {}
        self.few_shot_examples: Dict[str, List[Dict[str, str]]] = {}
        self.load_all()

    def load_all(self):
        """Loads all YAML files from the prompts directory."""
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir, exist_ok=True)
            return

        for filename in os.listdir(self.prompts_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(self.prompts_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = yaml.safe_load(f)
                        if data:
                            self.prompts.update(data)
                    except yaml.YAMLError as exc:
                        logger.error(f"Error loading prompt file {filename}: {exc}")
                        
        # Load auto-correction few-shots if they exist
        self.few_shot_file = os.path.join(self.prompts_dir, "auto_corrections.json")
        if os.path.exists(self.few_shot_file):
            try:
                with open(self.few_shot_file, 'r', encoding='utf-8') as f:
                    self.few_shot_examples = json.load(f)
            except Exception as e:
                logger.error(f"Error loading few-shot corrections: {e}")

    def add_few_shot_correction(self, prompt_key: str, bad_input: str, good_output: str):
        """Enregistre une auto-correction pour éviter de répéter une erreur (Metacognition)."""
        if prompt_key not in self.few_shot_examples:
            self.few_shot_examples[prompt_key] = []
            
        self.few_shot_examples[prompt_key].append({
            "input": bad_input,
            "expected": good_output
        })
        
        # Keep only the last 5 corrections to avoid prompt bloat
        self.few_shot_examples[prompt_key] = self.few_shot_examples[prompt_key][-5:]
        
        lock_path = f"{self.few_shot_file}.lock"
        lock = FileLock(lock_path, timeout=5)
        try:
            with lock:
                with open(self.few_shot_file, 'w', encoding='utf-8') as f:
                    json.dump(self.few_shot_examples, f, ensure_ascii=False, indent=2)
                logger.info(f"🧠 Metacognition: New self-correction saved for {prompt_key}.")
        except Timeout:
            logger.error(f"Timeout acquiring lock for {self.few_shot_file}")
        except Exception as e:
            logger.error(f"Failed to save correction: {e}")

    def update_system_prompt(self, key: str, new_system_prompt: str):
        """Met à jour (et persiste) le system prompt pour une clé donnée."""
        if key not in self.prompts:
            self.prompts[key] = {"template": "{context}"}
        
        if isinstance(self.prompts[key], str):
             self.prompts[key] = {"template": self.prompts[key]}
        
        self.prompts[key]["system_prompt"] = new_system_prompt
        
        # Persistance dans un fichier d'overrides
        overrides_path = os.path.join(self.prompts_dir, "dpo_optimized_prompts.yaml")
        
        lock_path = f"{overrides_path}.lock"
        lock = FileLock(lock_path, timeout=5)
        
        try:
            with lock:
                overrides = {}
                if os.path.exists(overrides_path):
                    with open(overrides_path, 'r', encoding='utf-8') as f:
                        try:
                            overrides = yaml.safe_load(f) or {}
                        except Exception as e:
                            logger.error(f"Error loading overrides: {e}")
                            overrides = {}
                
                overrides[key] = self.prompts[key]
                
                with open(overrides_path, 'w', encoding='utf-8') as f:
                    yaml.dump(overrides, f, allow_unicode=True)
                    
                logger.info(f"🚀 Prompt '{key}' optimized and saved to {overrides_path}")
        except Timeout:
            logger.error(f"Timeout acquiring lock for {overrides_path}")
        except Exception as e:
            logger.error(f"Error updating system prompt: {e}")

    def get_prompt(self, key: str, **kwargs) -> Any:
        """
        Retrieves a prompt by key, formats it, and appends dynamic few-shot examples if available.
        """
        prompt_template = self.prompts.get(key)
        if prompt_template is None:
            return f"Prompt for key '{key}' not found.", ""
        
        template = prompt_template if isinstance(prompt_template, str) else prompt_template.get("template", "")
        system = prompt_template.get("system_prompt", "") if isinstance(prompt_template, dict) else ""
        
        formatted_prompt = template.format(**kwargs)
        
        # --- SELF-EVOLVING: INJECTION DES FEW-SHOTS ---
        if key in self.few_shot_examples and self.few_shot_examples[key]:
            few_shot_text = "\n\n--- EXEMPLES À SUIVRE (Apprentissage des erreurs passées) ---\n"
            for ex in self.few_shot_examples[key]:
                few_shot_text += f"Exemple Input:\n{ex['input']}\nExemple Résultat Attendu:\n{ex['expected']}\n\n"
            system += few_shot_text
            
        return formatted_prompt, system

    def get_system_prompt(self, key: str, **kwargs) -> str:
        """Retrieves only the system prompt for a key."""
        prompt_template = self.prompts.get(key)
        if isinstance(prompt_template, dict):
            return prompt_template.get("system_prompt", "").format(**kwargs)
        return ""
