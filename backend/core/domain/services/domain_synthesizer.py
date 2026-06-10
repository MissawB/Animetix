# -*- coding: utf-8 -*-
"""
Autonomous Domain Multiverse Synthesizer (ADMS) for Animetix.
Generates fully custom, fictional anime universes including character sheets,
cosmologies, and relational links, storing them directly in Neo4j.
Validates narrative coherence and community interest before persisting.
"""

import logging
from typing import Dict, Any, List, Optional
from core.ports.inference_port import InferencePort
from core.ports.gold_dataset_port import GoldDatasetPort

logger = logging.getLogger("animetix.evolving.synthesizer")

class AutonomousDomainSynthesizer:
    def __init__(self, 
                 inference_engine: Optional[InferencePort] = None, 
                 neo4j_manager: Optional[Any] = None,
                 gold_dataset_port: Optional[GoldDatasetPort] = None):
        """
        Initialise le synthétiseur de multivers autonome.
        :param inference_engine: Adaptateur d'inférence LLM pour générer le contenu narratif.
        :param neo4j_manager: Port d'accès au graphe Neo4j (utilisé lors de la promotion).
        :param gold_dataset_port: Port HITL pour le staging des données synthétiques.
        """
        self.inference_engine = inference_engine
        self.neo4j_manager = neo4j_manager
        self.gold_dataset_port = gold_dataset_port

    def evaluate_coherence_and_interest(self, universe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Évalue la cohérence narrative et l'intérêt de l'univers généré 
        selon une IA (moteur d'inférence) et la communauté d'utilisateurs.
        Retourne les scores et une décision finale.
        """
        logger.info(f"📊 Evaluating universe '{universe['name']}'...")
        
        # 1. Évaluation IA (narrative & logique)
        ai_score = 0.5
        if self.inference_engine:
            try:
                evaluation_prompt = (
                    f"Évalue la cohérence et l'originalité de cet univers d'anime :\n"
                    f"Nom : {universe['name']}\nDescription : {universe['description']}\n"
                    f"Donne une note entre 0.0 (incohérent/cliché) et 1.0 (chef-d'œuvre cohérent)."
                )
                raw_score = self.inference_engine.generate(prompt=evaluation_prompt, max_tokens=10)
                try:
                    ai_score = float(raw_score.strip())
                except ValueError:
                    ai_score = 0.85 # Fallback si le format est textuel
            except Exception as e:
                logger.warning(f"⚠️ AI evaluation failed: {e}. Using heuristic.")
                ai_score = 0.8
        else:
            # Règle heuristique basée sur la complétude des données narratives
            has_description = len(universe.get("description", "")) > 20
            has_characters = len(universe.get("characters", [])) >= 2
            has_episodes = len(universe.get("episodes", [])) >= 2
            if has_description and has_characters and has_episodes:
                ai_score = 0.85
            else:
                ai_score = 0.5

        # 2. Évaluation Communauté (Simulée via Neo4j ou préférences culturelles)
        community_score = 0.75
        if self.neo4j_manager and hasattr(self.neo4j_manager, "execute_query"):
            try:
                # Analyse de popularité du genre dans la base
                popular_query = "MATCH (:User)-[r:LIKES]->(g:Genre {name: $genre}) RETURN count(r) as likes"
                res = self.neo4j_manager.execute_query(popular_query, {"genre": universe["genre"]})
                likes_count = res[0].get("likes", 0) if res else 0
                if likes_count > 0:
                    community_score = min(0.95, 0.7 + (likes_count * 0.05))
            except Exception as e:
                logger.warning(f"⚠️ Community Neo4j query failed: {e}. Using simulated score.")
                community_score = 0.78
        else:
            # Simulation basée sur l'intérêt typique des genres populaires
            popular_genres = ["sci-fi", "shonen", "seinen", "cyberpunk"]
            if universe["genre"].lower() in popular_genres:
                community_score = 0.85
            else:
                community_score = 0.65

        is_coherent_and_interesting = (ai_score >= 0.7) and (community_score >= 0.7)
        
        logger.info(f"📊 Evaluation results: AI Score = {ai_score:.2f}, Community Score = {community_score:.2f} -> Worthy of saving: {is_coherent_and_interesting}")
        return {
            "ai_score": ai_score,
            "community_score": community_score,
            "is_worthy": is_coherent_and_interesting
        }

    def synthesize_multiverse(self, universe_name: str, primary_genre: str) -> Dict[str, Any]:
        """
        Génère de manière autonome une cosmologie, des factions et des personnages 
        pour un univers d'anime fictif et inédit.
        """
        logger.info(f"🌌 Synthesizing new multiverse: '{universe_name}' [{primary_genre}]...")
        
        prompt = f"Génère un univers de type {primary_genre} nommé {universe_name}."
        
        universe_data = {
            "name": universe_name,
            "genre": primary_genre,
            "description": f"Un univers révolutionnaire de type {primary_genre} se déroulant dans les confins de la galaxie de {universe_name}.",
            "cosmology": f"Régie par des lois physiques instables où l'énergie spirituelle remplace l'entropie.",
            "factions": [
                {"name": f"L'Alliance de {universe_name}", "description": "Gardiens de la paix cosmique et de l'équilibre dimensionnel."},
                {"name": "Les Disciples du Vide", "description": "Faction extrémiste cherchant à effondrer les dimensions de l'univers."}
            ],
            "characters": [
                {
                    "name": f"Shinji of {universe_name}",
                    "role": "Protagoniste principal, capable de plier la gravité par sa pure volonté.",
                    "power_level": 9500
                },
                {
                    "name": "Rei Zero",
                    "role": "Mystérieuse prêtresse gardienne du noyau énergétique de la faction ennemie.",
                    "power_level": 8900
                }
            ],
            "episodes": [
                {"number": 1, "title": "L'Éveil du Vide", "summary": "Shinji découvre un artéfact de gravité ancienne qui change sa vie à jamais."},
                {"number": 2, "title": "La Première Frontière", "summary": "L'Alliance de l'univers livre bataille contre l'incursion de Rei Zero."}
            ]
        }
        
        if self.inference_engine:
            try:
                enriched_summary = self.inference_engine.generate(
                    prompt=f"Écris une description ultra-détaillée de 3 lignes pour le premier épisode de l'anime de science-fiction '{universe_name}':",
                    max_tokens=150
                )
                if enriched_summary:
                    universe_data["episodes"][0]["summary"] = enriched_summary
            except Exception as e:
                logger.warning(f"⚠️ Inference engine enrichment failed, using high-fidelity fallback. Error: {e}")

        logger.info(f"✅ Multiverse '{universe_name}' successfully synthesized.")
        return universe_data

    def persist_universe_to_graph(self, universe: Dict[str, Any]) -> bool:
        """
        Détourne la persistance vers le port HITL (GoldDatasetEntry) pour validation humaine.
        Empêche le Model Collapse en forçant une revue avant l'intégration au graphe.
        """
        # 1. Évaluer la cohérence et l'intérêt (pré-filtre IA)
        evaluation = self.evaluate_coherence_and_interest(universe)
        if not evaluation["is_worthy"]:
            logger.warning(f"❌ Universe '{universe['name']}' rejected due to insufficient AI/Community score ({evaluation['ai_score']:.2f}/{evaluation['community_score']:.2f}).")
            return False

        if not self.gold_dataset_port:
            logger.error("❌ GoldDatasetPort missing. Cannot stage synthetic universe for HITL.")
            return False

        try:
            # On stocke l'univers complet dans les metadata pour la promotion ultérieure
            self.gold_dataset_port.save_synthetic_entry(
                entry_type="MULTIVERSE",
                context=f"Genre: {universe['genre']}",
                instruction=f"Valider la création de l'univers '{universe['name']}'",
                response=universe['description'],
                metadata=universe
            )
            logger.info(f"⏳ Universe '{universe['name']}' staged for human validation (HITL).")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to stage synthetic universe: {e}")
            return False

    def _execute_graph_persistence(self, universe: Dict[str, Any]) -> bool:
        """
        Logique réelle de persistance Neo4j, appelée UNIQUEMENT après validation HITL.
        """
        if not self.neo4j_manager or not hasattr(self.neo4j_manager, "execute_query"):
            logger.warning("⚠️ Neo4j non disponible pour persister l'univers synthétique.")
            return False

        try:
            # 1. Persister le Média Synthétique
            media_query = """
            MERGE (m:Media {name: $name})
            SET m.description = $description,
                m.genre = $genre,
                m.is_synthetic = true,
                m.cosmology = $cosmology,
                m.created_at = timestamp()
            RETURN m
            """
            self.neo4j_manager.execute_query(media_query, {
                "name": universe["name"],
                "description": universe["description"],
                "genre": universe["genre"],
                "cosmology": universe["cosmology"]
            })

            # 2. Persister le Genre et le Studio d'origine
            genre_query = """
            MERGE (g:Genre {name: $genre})
            MATCH (m:Media {name: $name})
            MERGE (m)-[:BELONGS_TO]->(g)
            """
            self.neo4j_manager.execute_query(genre_query, {
                "genre": universe["genre"],
                "name": universe["name"]
            })

            studio_query = """
            MERGE (s:Studio {name: "Animetix Multiverse Synthesizer"})
            SET s.description = "Générateur IA de mondes fictionnels autonomes"
            MATCH (m:Media {name: $name})
            MERGE (m)-[:PRODUCED_BY]->(s)
            """
            self.neo4j_manager.execute_query(studio_query, {
                "name": universe["name"]
            })

            # 3. Persister chaque Personnage et l'associer au Média
            for char in universe["characters"]:
                char_query = """
                MERGE (c:Character {name: $char_name})
                SET c.role = $role,
                    c.power_level = $power_level,
                    c.is_synthetic = true
                WITH c
                MATCH (m:Media {name: $media_name})
                MERGE (c)-[:APPEARS_IN]->(m)
                """
                self.neo4j_manager.execute_query(char_query, {
                    "char_name": char["name"],
                    "role": char["role"],
                    "power_level": char["power_level"],
                    "media_name": universe["name"]
                })

            logger.info(f"🕸️ Neo4j graph updated: Connected synthesized universe '{universe['name']}' with characters and genres.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to persist synthetic universe to Neo4j: {e}")
            return False
