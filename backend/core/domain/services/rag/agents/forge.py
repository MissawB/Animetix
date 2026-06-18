import logging
import re
from typing import List, Optional

import orjson

from backend.core.domain.entities.ai_schemas import ForgeHypothesis
from backend.core.domain.services.llm_service import LLMService
from backend.core.domain.services.prompt_manager import PromptManager
from backend.core.ports.graph_persistence_port import GraphPersistencePort

logger = logging.getLogger("animetix.rag.forge")

# Common capitalized words to filter out from entity extraction
ENTITY_BLACKLIST = {
    "Who",
    "What",
    "When",
    "The",
    "How",
    "An",
    "Anime",
    "Manga",
    "If",
    "Why",
    "Where",
    "Which",
}


class ForgeAgent:
    def __init__(
        self,
        llm_service: LLMService,
        prompt_manager: PromptManager,
        neo4j_manager: GraphPersistencePort,
    ):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.neo4j_manager = neo4j_manager

    def generate_hypothesis(
        self, query: str, context: str
    ) -> Optional[ForgeHypothesis]:
        """
        Identifies patterns in the context/graph and generates logical hypotheses.
        """
        # Extract potential entities from query (Capitalized words)
        potential_entities = re.findall(r"\b[A-Z][a-zA-Z]{1,}\b", query)
        entities = [e for e in set(potential_entities) if e not in ENTITY_BLACKLIST]

        # Enrich context with historical patterns from Neo4j
        pattern_context = self._fetch_patterns(entities)
        if pattern_context:
            context = f"{context}\n\nHistorical Patterns:\n{pattern_context}"

        prompt, sys = self.prompt_manager.get_prompt(
            "forge_speculation", query=query, context=context
        )
        res_raw = self.llm_service.generate(prompt, system_prompt=sys, use_slm=True)

        try:
            # Find the JSON block in case there's preamble/postamble
            if "{" in res_raw and "}" in res_raw:
                json_str = res_raw[res_raw.find("{") : res_raw.rfind("}") + 1]
                data = orjson.loads(json_str)

                # Pydantic validation
                return ForgeHypothesis(**data)
            return None
        except Exception as e:
            logger.error(f"Failed to parse Forge hypothesis: {e}")
            return None

    def _fetch_patterns(self, entities: List[str]) -> str:
        """
        Search Neo4j for previous releases of the same studio/author to provide 'pattern context'.
        """
        if not self.neo4j_manager or not entities:
            return ""

        query = """
        MATCH (e)<-[:PRODUCED_BY|CREATED_BY]-(m:Media)
        WHERE e.name IN $names
        RETURN e.name as entity, m.title as title, m.year as year
        ORDER BY m.year DESC
        """
        results = self.neo4j_manager.execute_query(query, {"names": entities})

        if not results:
            return ""

        grouped = {}
        for r in results:
            entity = r["entity"]
            if entity not in grouped:
                grouped[entity] = []
            if len(grouped[entity]) < 5:
                grouped[entity].append(f"{r['title']} ({r['year']})")

        patterns = []
        for entity, works in grouped.items():
            patterns.append(f"Entity '{entity}' past works: {', '.join(works)}")

        return "\n".join(patterns)
