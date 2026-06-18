import logging
from typing import Any, Dict, List

import orjson
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager
from core.ports.graph_persistence_port import GraphPersistencePort
from core.ports.web_search_port import WebSearchPort

logger = logging.getLogger("animetix.rag.chronicler")


class ChroniclerAgent:
    def __init__(
        self,
        llm_service: LLMService,
        prompt_manager: PromptManager,
        neo4j_manager: GraphPersistencePort,
        web_search: WebSearchPort,
    ) -> None:
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.neo4j_manager = neo4j_manager
        self.web_search = web_search

    def extract_theories(
        self, saga_name: str, source_text: str
    ) -> List[Dict[str, Any]]:
        prompt, sys = self.prompt_manager.get_prompt(
            "chronicler_extraction", source_text=source_text
        )
        res_raw = self.llm_service.generate(prompt, sys, use_slm=True)

        try:
            start_idx = min(
                [idx for idx in [res_raw.find("{"), res_raw.find("[")] if idx != -1]
                or [-1]
            )
            end_idx = max(res_raw.rfind("}"), res_raw.rfind("]"))

            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = res_raw[start_idx : end_idx + 1]
                data = orjson.loads(json_str)
                # The prompt returns {"theories": [...]}. Handle if it returned a list directly.
                if isinstance(data, dict):
                    return data.get("theories", [])
                elif isinstance(data, list):
                    return data
            return []
        except Exception as e:
            logger.error(f"Failed to parse theories from LLM: {e}")
            return []

    def pulse_community(self, saga_name: str) -> None:
        """Scans the web for community lore and updates Neo4j."""
        logger.info(f"📡 [Chronicler] Pulsing community lore for {saga_name}...")

        search_query = f"{saga_name} fan theories explained consensus reddit"
        results = self.web_search.search(search_query)

        if not results:
            logger.warning(f"No community data found for {saga_name}.")
            return

        compiled_text = "\n".join(
            [f"[{r.get('title', 'Unknown')}] {r.get('snippet', '')}" for r in results]
        )

        theories = self.extract_theories(saga_name, compiled_text)
        logger.info(f"⚖️ [Chronicler] Extracted {len(theories)} theories. Syncing...")

        for theory in theories:
            try:
                theory["source_url"] = (
                    results[0].get("link", "Web Search") if results else "Unknown"
                )
                self.neo4j_manager.sync_fan_theory(saga_name, theory)
            except Exception as e:
                logger.error(
                    f"Failed to sync theory {theory.get('title')} to Neo4j: {e}"
                )

        logger.info("✅ Community pulse complete.")
