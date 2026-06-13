import os
import sys
import re
import json
import logging
from typing import List, Dict, Optional

# Configuration des chemins d'importation
BASE_DIR = r"C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project"
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "pipeline", "mlops"))

# Configuration Django
logger = logging.getLogger("animetix.mlops.knowledge_indexer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
try:
    django.setup()
    from animetix.containers import get_container
except Exception as e:
    logger.warning(f"Django init warning: {e}. Running in standalone simulated mode.")
    get_container = None

# Importation dynamique sécurisée des 7 bases de données d'élite locales
try:
    from creators_db import CREATORS_AND_STUDIOS
    from songs_and_seiyuu_db import ANIME_SONGS_AND_SINGERS, SEIYUU_PROFILES, SONGS_AND_SEIYUU_RELATIONS
    from magazines_and_awards_db import SERIALIZATION_MAGAZINES, POP_CULTURE_AWARDS, AWARDS_AND_MAGAZINES_RELATIONS
    from french_market_db import (
        FRENCH_VOICE_ACTORS,
        FRENCH_MANGA_PUBLISHERS,
        FRENCH_ANIME_DISTRIBUTORS,
        FRENCH_MARKET_RELATIONS
    )
    from japanese_market_db import (
        JAPANESE_MANGA_PUBLISHERS,
        JAPANESE_ANIME_DISTRIBUTORS,
        JAPANESE_MARKET_RELATIONS
    )
    from volumes_and_episodes_db import VOLUMES_AND_EPISODES_DATA
    from transmedia_db import TRANSMEDIA_RELATIONS
except ImportError as e:
    logger.error(f"Failed to import local meta databases: {e}")
    sys.exit(1)

class OtakuKnowledgeIndexer:
    """
    Indexeur sémantique de masse de la connaissance Otaku unifiée.
    Compile les 6 bases de données locales de métadonnées et les indexe dans ChromaDB.
    """
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.container = get_container() if get_container else None

    def compile_all_facts(self) -> List[Dict[str, str]]:
        """Agrége et structure toutes les connaissances métas sous forme de faits sémantiques riches."""
        facts = []
        
        # 1. Artistes Anisongs
        for name, details in ANIME_SONGS_AND_SINGERS.items():
            text = f"Artiste Anisong : {name}. Définition : {details.get('definition', '')} Origine : {details.get('origin', '')} Œuvres cultes : {details.get('examples', '')} Impact : {details.get('impact', '')}"
            facts.append({"category": "Anisong Artists", "title": name, "content": text})

        # 2. Seiyuu Japonais
        for name, details in SEIYUU_PROFILES.items():
            text = f"Acteur de doublage japonais (Seiyuu) : {name}. Rôle et profil : {details.get('definition', '')} Origine et carrière : {details.get('origin', '')} Doublages cultes : {details.get('examples', '')} Impact : {details.get('impact', '')}"
            facts.append({"category": "Seiyuu Profiles", "title": name, "content": text})

        # 3. Créateurs & Mangakas
        for name, details in CREATORS_AND_STUDIOS.items():
            text = f"Créateur de l'industrie (Mangaka / Réalisateur) : {name}. Biographie : {details.get('definition', '')} Origine : {details.get('origin', '')} Chefs-d'œuvre : {details.get('examples', '')} Style et impact : {details.get('impact', '')}"
            facts.append({"category": "Creators & Directors", "title": name, "content": text})

        # 4. Doublage Français (Comédiens VF)
        for name, details in FRENCH_VOICE_ACTORS.items():
            text = f"Comédien de doublage français (VF) : {name}. Profil vocal : {details.get('definition', '')} Carrière : {details.get('origin', '')} Rôles VF mythiques : {details.get('examples', '')} Impact sur la VF : {details.get('impact', '')}"
            facts.append({"category": "French Voice Actors (VF)", "title": name, "content": text})

        # 5. Éditeurs Français de Mangas
        for name, details in FRENCH_MANGA_PUBLISHERS.items():
            text = f"Maison d'édition de manga en France : {name}. Présentation : {details.get('definition', '')} Historique de fondation : {details.get('origin', '')} Titres phares du catalogue : {details.get('examples', '')} Impact sur le marché VF : {details.get('impact', '')}"
            facts.append({"category": "French Manga Publishers", "title": name, "content": text})

        # 6. Distributeurs & Plateformes de Streaming en France
        for name, details in FRENCH_ANIME_DISTRIBUTORS.items():
            text = f"Distributeur et diffuseur d'anime en France : {name}. Présentation : {details.get('definition', '')} Origine de la plateforme : {details.get('origin', '')} Catalogues et exclusivités : {details.get('examples', '')} Impact de diffusion : {details.get('impact', '')}"
            facts.append({"category": "French Anime Distributors", "title": name, "content": text})

        # 6b. Éditeurs Japonais de Mangas (Symmetrie Japon)
        for name, details in JAPANESE_MANGA_PUBLISHERS.items():
            text = f"Maison d'édition de manga au Japon : {name}. Présentation : {details.get('definition', '')} Historique de fondation : {details.get('origin', '')} Titres phares du catalogue : {details.get('examples', '')} Impact sur le marché japonais : {details.get('impact', '')}"
            facts.append({"category": "Japanese Manga Publishers", "title": name, "content": text})

        # 6c. Distributeurs & Plateformes au Japon (Symmetrie Japon)
        for name, details in JAPANESE_ANIME_DISTRIBUTORS.items():
            text = f"Distributeur et diffuseur d'anime au Japon : {name}. Présentation : {details.get('definition', '')} Origine de la plateforme : {details.get('origin', '')} Catalogues et exclusivités : {details.get('examples', '')} Impact de diffusion : {details.get('impact', '')}"
            facts.append({"category": "Japanese Anime Distributors (JP)", "title": name, "content": text})

        # 7. Prix Littéraires & Récompenses
        for name, details in POP_CULTURE_AWARDS.items():
            text = f"Prix prestigieux de la pop-culture (Manga/Anime) : {name}. Définition : {details.get('definition', '')} Historique et origine : {details.get('origin', '')} Lauréats historiques majeurs : {details.get('examples', '')} Impact sur l'industrie : {details.get('impact', '')}"
            facts.append({"category": "Pop-Culture Awards", "title": name, "content": text})

        # 8. Magazines de Prépublication Japonais
        for name, details in SERIALIZATION_MAGAZINES.items():
            text = f"Magazine de prépublication de manga japonais : {name}. Profil éditorial : {details.get('definition', '')} Historique et éditeur : {details.get('origin', '')} Mangas cultes sérialisés : {details.get('examples', '')} Impact culturel : {details.get('impact', '')}"
            facts.append({"category": "Serialization Magazines", "title": name, "content": text})

        # 9. Statistiques de Volumes & Épisodes
        for key, details in VOLUMES_AND_EPISODES_DATA.items():
            text = f"Statistiques d'adaptation et volumes physiques : {key}. Détails : {details.get('definition', '')} Épisodes d'adaptation animée : {details.get('origin', '')} Tomes de manga papier : {details.get('examples', '')} Comparaison transmédiatique : {details.get('impact', '')}"
            facts.append({"category": "Volumes & Episodes Stats", "title": key, "content": text})

        # 10. Relations Complexes (Anisongs, Seiyuu, French Market, Japanese Market, Transmedia)
        all_relations = (
            SONGS_AND_SEIYUU_RELATIONS + 
            AWARDS_AND_MAGAZINES_RELATIONS + 
            FRENCH_MARKET_RELATIONS + 
            JAPANESE_MARKET_RELATIONS +
            TRANSMEDIA_RELATIONS
        )
        for rel in all_relations:
            if "question" in rel and "answer" in rel:
                title = f"Relation : {rel['question'][:100]}"
                content = f"Question : {rel['question']} Réponse : {rel['answer']}"
            else:
                title = f"Relation sémantique {rel.get('source', '')} - {rel.get('target', '')}"
                content = f"Fait relationnel Otaku expert : {rel.get('relation_text', '')}"
            facts.append({
                "category": "Expert Transmedia Relations",
                "title": title,
                "content": content
            })
            
        return facts

    def chunk_ssemantic(self, text: str, size: int = 400) -> List[str]:
        """Segmentation sémantique par phrase complete."""
        sentence_end = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_end.split(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if current_length + len(sentence) > size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def execute_indexation(self):
        """Exécute la compilation et l'indexation de masse unifiée."""
        logger.info("🚀 Compiling expert Otaku knowledge bases...")
        facts = self.compile_all_facts()
        logger.info(f"📊 Successfully compiled {len(facts)} expert factual entries.")
        
        indexed_count = 0
        
        if self.dry_run:
            logger.info("🧪 [Dry-Run] Simulating indexation of all entries...")
            for f in facts[:5]:
                logger.info(f"👉 Category: {f['category']} | Title: {f['title']}")
                logger.info(f"   Sample fact: {f['content'][:150]}...")
            logger.info(f"✨ Simulating finished for {len(facts)} compiled factual entries.")
            return

        if not self.container:
            logger.error("❌ Django Container is not initialized. Cannot run indexation in production.")
            return

        try:
            repo = self.container.repository()
            # On indexe l'intégralité dans la collection 'anime_thematic'
            collection_name = repo.chroma.coll_names.get('Anime', 'anime_thematic')
            
            ids = []
            embeddings = []
            metadatas = []
            
            embedding_fn = repo.chroma.embedding_fn
            
            logger.info("🏋️ Vectorizing all factual entries using Jina-v3 locally...")
            
            for entry in facts:
                # Contextual Retrieval : prépendre un entête de catégorie riche
                context_header = f"[Source: Otaku Database | Catégorie: {entry['category']} | Sujet: {entry['title']}] "
                
                # Découpage sémantique par phrase
                chunks = self.chunk_ssemantic(entry["content"], size=400)
                
                for i, chunk in enumerate(chunks):
                    chunk_text = context_header + chunk
                    doc_id = f"meta_{entry['category'].lower().replace(' ', '_')}_{hash(entry['title'])}_{i}"
                    
                    # Calcul de l'embedding
                    vector = embedding_fn([chunk_text])[0]
                    
                    ids.append(doc_id)
                    embeddings.append(list(vector))
                    metadatas.append({
                        "title": f"Expert Meta: {entry['title']}",
                        "description": chunk_text,
                        "source": "Otaku Meta Database",
                        "category": entry["category"]
                    })
            
            # Upsert en masse dans ChromaDB via le repository
            repo.chroma.upsert_items(collection_name, ids, embeddings, metadatas)
            logger.info(f"✅ Upserted {len(ids)} expert factual chunks into ChromaDB.")
            indexed_count = len(ids)
        except Exception as e:
            logger.error(f"❌ Failed to execute mass indexation in ChromaDB: {e}")
            
        logger.info(f"✨ Otaku Knowledge Indexer finished. Processed {indexed_count} total ssemantic chunks.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Indexation de masse de la base Otaku unifiée.")
    parser.add_argument("--dry-run", action="store_true", help="Simule l'indexation sans écrire dans ChromaDB.")
    args = parser.parse_args()
    
    indexer = OtakuKnowledgeIndexer(dry_run=args.dry_run)
    indexer.execute_indexation()
