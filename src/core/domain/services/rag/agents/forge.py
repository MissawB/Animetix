import logging
import re
from typing import Dict, Optional, Any, List
from src.core.domain.services.llm_service import LLMService
from src.core.domain.services.prompt_manager import PromptManager
from src.pipeline.neo4j_client import Neo4jManager

logger = logging.getLogger("animetix.rag.forge")

class ForgeAgent:
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager, neo4j_manager: Neo4jManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.neo4j_manager = neo4j_manager

    def generate_hypothesis(self, query: str, context: str) -> Optional[Dict[str, Any]]:
        """
        Identifies patterns in the context/graph and generates logical hypotheses.
        """
        # Extract potential entities from query (Capitalized words)
        potential_entities = re.findall(r'\b[A-Z][a-zA-Z]{1,}\b', query)
        entities = list(set(potential_entities))
        
        # Enrich context with historical patterns from Neo4j
        pattern_context = self._fetch_patterns(entities)
        if pattern_context:
            context = f"{context}\n\nHistorical Patterns:\n{pattern_context}"
        
        prompt, sys = self.prompt_manager.get_prompt("forge_speculation", query=query, context=context)
        res_raw = self.llm_service.generate(prompt, system_prompt=sys, use_slm=True)
        
        try:
            import orjson
            # Find the JSON block in case there's preamble/postamble
            if '{' in res_raw and '}' in res_raw:
                json_str = res_raw[res_raw.find('{'):res_raw.rfind('}')+1]
                data = orjson.loads(json_str)
                
                # Robust validation: hypothesis and rationale are mandatory
                if all(k in data for k in ["hypothesis", "rationale"]):
                    return data
                else:
                    logger.warning(f"Forge hypothesis missing required fields: {list(data.keys())}")
                    return None
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
            entity = r['entity']
            if entity not in grouped:
                grouped[entity] = []
            if len(grouped[entity]) < 5:
                grouped[entity].append(f"{r['title']} ({r['year']})")
        
        patterns = []
        for entity, works in grouped.items():
            patterns.append(f"Entity '{entity}' past works: {', '.join(works)}")
            
        return "\n".join(patterns)
