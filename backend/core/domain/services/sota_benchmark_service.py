import logging
from typing import List, Dict, Any

logger = logging.getLogger("animetix.mlops.sota")


class SOTABenchmarkService:
    """
    Fournit les benchmarks SOTA (State of the Art) pour les modèles IA.
    Centralise les scores HuggingFace Best, Chatbot Arena ELO et capacités techniques.
    """

    def __init__(self):
        # Données SOTA (simulées basées sur les tendances 2026)
        self._benchmarks = [
            {
                "model_id": "Qwen/Qwen2.5-72B-Instruct",
                "provider": "Alibaba",
                "huggingface_id": "Qwen/Qwen2.5-72B-Instruct",
                "elo_score": 1315,
                "mmlu_score": 86.2,
                "context_window": 128000,
                "license": "Apache 2.0",
                "is_open_source": True,
                "status": "Active",
            },
            {
                "model_id": "meta-llama/Llama-3.1-405B-Instruct",
                "provider": "Meta",
                "huggingface_id": "meta-llama/Llama-3.1-405B-Instruct",
                "elo_score": 1332,
                "mmlu_score": 88.6,
                "context_window": 128000,
                "license": "Llama 3.1",
                "is_open_source": True,
                "status": "Active",
            },
            {
                "model_id": "gpt-4o",
                "provider": "OpenAI",
                "huggingface_id": None,
                "elo_score": 1350,
                "mmlu_score": 88.7,
                "context_window": 128000,
                "license": "Proprietary",
                "is_open_source": False,
                "status": "Active",
            },
            {
                "model_id": "claude-3-5-sonnet-20240620",
                "provider": "Anthropic",
                "huggingface_id": None,
                "elo_score": 1345,
                "mmlu_score": 88.0,
                "context_window": 200000,
                "license": "Proprietary",
                "is_open_source": False,
                "status": "Active",
            },
            {
                "model_id": "mistralai/Mistral-Large-2",
                "provider": "Mistral AI",
                "huggingface_id": "mistralai/Mistral-Large-Instruct-2407",
                "elo_score": 1290,
                "mmlu_score": 84.0,
                "context_window": 128000,
                "license": "Mistral Research",
                "is_open_source": True,
                "status": "Active",
            },
            {
                "model_id": "deepseek-ai/DeepSeek-V2.5",
                "provider": "DeepSeek",
                "huggingface_id": "deepseek-ai/DeepSeek-V2.5",
                "elo_score": 1305,
                "mmlu_score": 85.5,
                "context_window": 128000,
                "license": "MIT",
                "is_open_source": True,
                "status": "Active",
            },
        ]

    def get_all_benchmarks(self) -> List[Dict[str, Any]]:
        """Retourne la liste complète des benchmarks SOTA."""
        return self._benchmarks

    def get_best_model(self, criteria: str = "elo_score") -> Dict[str, Any]:
        """Retourne le meilleur modèle selon un critère donné."""
        try:
            return max(self._benchmarks, key=lambda x: x.get(criteria, 0))
        except Exception:
            return self._benchmarks[0]

    def get_open_source_best(self) -> List[Dict[str, Any]]:
        """Retourne les meilleurs modèles Open Source."""
        os_models = [m for m in self._benchmarks if m["is_open_source"]]
        return sorted(os_models, key=lambda x: x["elo_score"], reverse=True)
