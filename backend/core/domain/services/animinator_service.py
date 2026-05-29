import random
from typing import Dict, Optional, List, Tuple
from .llm_service import LLMService

class AniminatorDomainService:
    def __init__(self, llm_service: LLMService, neo4j_manager=None):
        self.llm_service = llm_service
        self.neo4j = neo4j_manager

    def select_secret(self, catalog: Dict) -> Optional[str]:
        if not catalog or 'title_to_full_data' not in catalog: return None
        items = list(catalog['title_to_full_data'].values())
        if not items: return None
        selected = random.choice(items)
        return selected.get('title')

    def _fetch_graph_facts(self, secret_title: str, question: str) -> str:
        """Interroge Neo4j pour trouver des faits pertinents à la question."""
        if not self.neo4j: return ""

        # On cherche des noms propres dans la question (simplifié)
        import re
        words = re.findall(r'\b[A-Z][a-z]+\b', question)

        facts = []
        for word in words:
            # Requête pour voir si le secret est lié à cette entité
            query = """
            MATCH (m:Media {title: $title})-[:FEATURES]->(e:Entity)
            WHERE e.name CONTAINS $word
            MATCH (e)-[r:AI_RELATION]-(other:Entity)
            RETURN e.name as ent, type(r) as rel, other.name as target
            LIMIT 3
            """
            res = self.neo4j.execute_query(query, {"title": secret_title, "word": word})
            for r in res:
                facts.append(f"- {r['ent']} est {r['rel']} de {r['target']}")

        return "\n".join(facts) if facts else ""

    def ask_oracle(self, media_type: str, title: str, full_data: Dict, question: str) -> str:
        """Pose une question à l'Oracle avec augmentation par le graphe."""
        facts = self._fetch_graph_facts(title, question)
        if facts:
            # On injecte les faits dans une version augmentée du prompt via le LLM service
            # (Note: idéalement le LLM service devrait accepter un paramètre 'context' ou 'facts')
            augmented_question = f"[FAITS RÉELS DU GRAPHE :\n{facts}]\n\nQUESTION : {question}"
            return self.llm_service.ask_oracle(media_type, title, augmented_question)

        return self.llm_service.ask_oracle(media_type, title, question)

    def ask_oracle_stream(self, media_type: str, title: str, question: str):
        """Version streaming de l'Oracle augmentée."""
        facts = self._fetch_graph_facts(title, question)
        if facts:
            question = f"[FAITS DU GRAPHE :\n{facts}]\n\n{question}"
        yield from self.llm_service.ask_oracle_stream(media_type, title, question)


    def check_guess(self, guess: str, secret: str) -> bool:
        """Vérifie si le guess correspond au titre secret."""
        return guess.strip().lower() == secret.strip().lower()
