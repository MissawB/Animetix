import logging
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
        # TODO: Optionally enrich context with _fetch_patterns
        # Example: extract entities from query to fetch patterns
        
        prompt, sys = self.prompt_manager.get_prompt("forge_speculation", query=query, context=context)
        res_raw = self.llm_service.generate(prompt, system_prompt=sys, use_slm=True)
        
        try:
            import orjson
            # Find the JSON block in case there's preamble/postamble
            if '{' in res_raw and '}' in res_raw:
                json_str = res_raw[res_raw.find('{'):res_raw.rfind('}')+1]
                data = orjson.loads(json_str)
                
                # Validation of required fields
                if all(k in data for k in ["hypothesis", "rationale", "confidence"]):
                    return data
                else:
                    logger.warning("Forge hypothesis missing required fields.")
                    return data # Still return if some fields are there, or could be more strict
            return None
        except Exception as e:
            logger.error(f"Failed to parse Forge hypothesis: {e}")
            return None

    def _fetch_patterns(self, entities: List[str]) -> str:
        """
        Search Neo4j for previous releases of the same studio/author to provide 'pattern context'.
        """
        if not self.neo4j_manager:
            return ""
            
        patterns = []
        for entity in entities:
            # Query to find other works by the same studio or creator
            query = """
            MATCH (e {name: $name})<-[:PRODUCED_BY|CREATED_BY]-(m:Media)
            RETURN m.title as title, m.year as year
            ORDER BY m.year DESC LIMIT 5
            """
            results = self.neo4j_manager.execute_query(query, {"name": entity})
            if results:
                works = [f"{r['title']} ({r['year']})" for r in results]
                patterns.append(f"Entity '{entity}' past works: {', '.join(works)}")
        
        return "\n".join(patterns)
