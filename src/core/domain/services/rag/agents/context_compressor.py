import logging
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.context_compressor")

class ContextCompressor:
    """
    Agent SOTA 2026 responsable de la compression sémantique du contexte brut (Context Prompt Compression).
    Élimine le bruit et les tokens redondants avant d'envoyer le contexte au distillateur Scout,
    réduisant ainsi la latence globale et le coût d'inférence.
    """
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def compress(self, query: str, context: str) -> str:
        """Compresse sémantiquement le contexte en éliminant les redondances et les tokens superflus."""
        if not context or len(context) < 300:
            return context

        logger.info(f"⚡ Context Compressor: Compressing raw context of length {len(context)}...")
        
        # 1. Filtre de déduplication local rapide
        lines = [line.strip() for line in context.split("\n") if line.strip()]
        unique_lines = []
        seen = set()
        for line in lines:
            # Nettoyage et vérification de doublons simples
            norm_line = line.lower()[:100]
            if norm_line not in seen:
                seen.add(norm_line)
                unique_lines.append(line)
                
        deduplicated = "\n".join(unique_lines)
        
        # Si le texte est déjà court après déduplication, pas besoin de compresser plus par LLM
        if len(deduplicated) < 500:
            return deduplicated

        # 2. Compression sémantique par SLM
        prompt = (
            f"Compresse le contexte brut suivant pour répondre à la question : \"{query}\".\n\n"
            f"Consignes de compression :\n"
            f"- Retire tous les mots superflus, les phrases redondantes, le bruit de scraping ou de métadonnées, et les formules de politesse.\n"
            f"- Conserve STRICTEMENT 100% des faits précis, noms d'auteurs, studios, dates, chiffres, doubleurs VF, seiyū, relations et terminologies techniques.\n"
            f"- Rends le texte le plus compact possible en conservant son intégrité factuelle.\n\n"
            f"CONTEXTE BRUT :\n{deduplicated}\n\n"
            f"Retourne uniquement le texte compressé final, sans préambule ni explications."
        )
        system_prompt = "Tu es un compresseur de prompt d'élite (LLMLingua approach). Retourne uniquement le texte compressé."

        try:
            compressed = self.llm_service.generate(prompt, system_prompt, use_slm=True)
            if compressed and len(compressed) > 100:
                reduction = (1 - len(compressed) / len(context)) * 100
                logger.info(f"✅ Context Compressor: Compressed context length from {len(context)} to {len(compressed)} (-{reduction:.1f}% tokens).")
                return compressed
            return deduplicated
        except Exception as e:
            logger.error(f"❌ Context Compressor failed: {e}. Falling back to deduplicated context.")
            return deduplicated
