import logging
import os
import re
import sys
from typing import List, Optional

try:
    from bs4 import BeautifulSoup  # noqa: E402
except ImportError:
    BeautifulSoup = None

# Configuration des chemins d'importation
BASE_DIR = r"C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project"
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "backend"))

# Configuration Django
import django  # noqa: E402
from core.utils.security import safe_http_request  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")

logger = logging.getLogger("animetix.pipeline." + __name__)

try:
    django.setup()
    from animetix.containers import get_container  # noqa: E402
    from animetix.models import MediaItem  # noqa: E402
except Exception as e:
    logger.warning(f"⚠️ Django init warning: {e}. Running in simulated catalog mode.")
    MediaItem = None
    get_container = None

# Mapping statique robuste des Fandoms pour les franchises clés (Fidélité 100%)
FANDOM_MAP = {
    "one piece": {
        "wiki_url": "https://onepiece.fandom.com/wiki/One_Piece",
        "subpages": ["Monkey_D._Luffy", "Roronoa_Zoro", "Devil_Fruit"],
    },
    "berserk": {
        "wiki_url": "https://berserk.fandom.com/wiki/Berserk",
        "subpages": ["Guts", "Griffith", "Dragon_Slayer"],
    },
    "neon genesis evangelion": {
        "wiki_url": "https://evangelion.fandom.com/wiki/Neon_Genesis_Evangelion",
        "subpages": ["Shinji_Ikari", "Asuka_Langley_Soryu", "Evangelion_Unit-01"],
    },
    "death note": {
        "wiki_url": "https://deathnote.fandom.com/wiki/Death_Note",
        "subpages": ["Light_Yagami", "L_(character)", "Death_Note_(object)"],
    },
    "demon slayer": {
        "wiki_url": "https://demonslayer-anime.fandom.com/wiki/Kimetsu_no_Yaiba",
        "subpages": ["Tanjiro_Kamado", "Nezuko_Kamado", "Muzan_Kibutsuji"],
    },
    "hunter x hunter": {
        "wiki_url": "https://hunterxhunter.fandom.com/wiki/Hunter_%C3%97_Hunter",
        "subpages": ["Gon_Freecss", "Killua_Zoldyck", "Nen"],
    },
    "naruto": {
        "wiki_url": "https://naruto.fandom.com/wiki/Naruto",
        "subpages": ["Naruto_Uzumaki", "Sasuke_Uchiha", "Chakra"],
    },
    "fullmetal alchemist": {
        "wiki_url": "https://fma.fandom.com/wiki/Fullmetal_Alchemist",
        "subpages": ["Edward_Elric", "Alphonse_Elric", "Alchemists"],
    },
}


class FandomLoreScraper:
    """
    Pipeline MLOps d'acquisition massive et d'enrichissement sémantique
    du lore d'animes et mangas à partir des wikis Fandom.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.container = get_container() if get_container else None

    def get_popular_franchises(self) -> List[str]:
        """Récupère la liste des franchises populaires du catalogue."""
        if MediaItem:
            try:
                # Filtrer les items les plus populaires
                items = MediaItem.objects.filter(popularity__gt=80).values_list(
                    "title", flat=True
                )[:15]
                result = list(set([t.lower().strip() for t in items]))
                if result:
                    return result
            except Exception as e:
                logger.error(f"Failed to query SQL MediaItems: {e}")

        # Fallback catalogue statique
        return list(FANDOM_MAP.keys())

    def scrape_url(self, url: str) -> Optional[str]:
        """Scrape une URL poliment et en extrait le contenu textuel sémantique."""
        logger.info(f"🕸️ Scraping: {url} ...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            response = safe_http_request("GET", url, headers=headers, timeout=10)
            html = response.content

            if BeautifulSoup:
                soup = BeautifulSoup(html, "html.parser")
                # Nettoyage du bruit HTML typique de Fandom (pubs, menus, scripts, asides)
                for tag in soup(["script", "style", "noscript", "iframe", "aside"]):
                    tag.decompose()

                # Cibler le contenu principal de l'article Fandom
                content_div = soup.find(id="mw-content-text") or soup.find(
                    class_="mw-parser-output"
                )
                if not content_div:
                    content_div = soup

                text = content_div.get_text(separator=" ")
            else:
                # Fallback Regex sémantique ultra-robuste en cas d'absence de BeautifulSoup
                html_str = html.decode("utf-8", errors="ignore")
                # Supprimer les balises scripts, styles et asides bruyantes de Fandom
                html_str = re.sub(
                    r"<(script|style|noscript|iframe|aside)[^>]*>.*?</\1>",
                    "",
                    html_str,
                    flags=re.DOTALL,
                )
                # Dépouiller toutes les autres balises HTML
                text = re.sub(r"<[^>]+>", " ", html_str)

            # Nettoyer les espaces multiples
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception as e:
            logger.error(f"❌ Failed to scrape {url}: {e}")
            return None

    def chunk_ssemantic(self, text: str, size: int = 500) -> List[str]:
        """Segmentation sémantique intelligente par phrases complètes."""
        sentence_end = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_end.split(text)

        chunks = []
        current_chunk: list[str] = []
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

    def execute_pipeline(self):
        """Lance l'acquisition, la distillation et la double indexation sémantique."""
        logger.info("🚀 Starting Fandom Lore Acquisition Pipeline...")
        franchises = self.get_popular_franchises()
        logger.info(f"📊 Found {len(franchises)} popular franchises to inspect.")

        indexed_count = 0

        for franchise in franchises:
            # Recherche d'un Fandom connu
            matched_key = None
            for key in FANDOM_MAP:
                if key in franchise or franchise in key:
                    matched_key = key
                    break

            if not matched_key:
                logger.info(
                    f"⏩ Franchise '{franchise}' has no predefined Fandom wiki map. Skipping."
                )
                continue

            info = FANDOM_MAP[matched_key]
            logger.info(f"🎯 Processing Lore for: {matched_key.upper()}...")

            # Scraper la page d'accueil de la franchise
            main_text = self.scrape_url(info["wiki_url"])
            texts_to_process = []
            if main_text:
                texts_to_process.append((info["wiki_url"], main_text))

            # Scraper les sous-pages de lore profond (personnages, objets, techniques)
            base_wiki = info["wiki_url"].rsplit("/", 1)[0]
            for sub in info["subpages"]:
                sub_url = f"{base_wiki}/{sub}"
                sub_text = self.scrape_url(sub_url)
                if sub_text:
                    texts_to_process.append((sub_url, sub_text))

            # Traiter et indexer chaque texte extrait
            for source_url, raw_text in texts_to_process:
                # Émonder le texte s'il est trop verbeux pour se concentrer sur l'essentiel
                clean_text = raw_text[
                    :8000
                ]  # focus sur les 8000 premiers caractères descriptifs

                # Contextual Retrieval : prépendre un entête de contexte riche
                context_header = f"[Source: Fandom Lore | Franchise: {matched_key.title()} | URL: {source_url}] "

                # Segmentation sémantique par phrase
                chunks = self.chunk_ssemantic(clean_text, size=400)

                logger.info(
                    f"⚙️ Distilled into {len(chunks)} contextual chunks for {source_url}."
                )

                if self.dry_run:
                    logger.info(
                        f"🧪 [Dry-Run] Sample Chunk: {context_header}{chunks[0][:150]}..."
                    )
                    indexed_count += len(chunks)
                    continue

                # Indexation pgvector réelle via le repository
                if self.container:
                    try:
                        repo = self.container.repository()
                        collection_name = repo.vectors.coll_names.get(
                            "Anime", "anime_thematic"
                        )

                        ids = []
                        embeddings = []
                        metadatas = []

                        # Récupérer l'adapter d'embeddings
                        embedding_fn = repo.vectors.embedding_fn

                        for i, chunk in enumerate(chunks):
                            chunk_text = context_header + chunk
                            doc_id = f"fandom_{matched_key}_{hash(source_url)}_{i}"

                            # Calcul de l'embedding
                            vector = embedding_fn([chunk_text])[0]

                            ids.append(doc_id)
                            embeddings.append(list(vector))
                            metadatas.append(
                                {
                                    "title": f"Lore {matched_key.title()}",
                                    "description": chunk_text,
                                    "source": "Fandom Scraping",
                                    "franchise": matched_key,
                                }
                            )

                        # Upsert dans pgvector
                        repo.vectors.upsert_items(
                            collection_name, ids, embeddings, metadatas
                        )
                        logger.info(
                            f"✅ Upserted {len(chunks)} lore chunks for {matched_key} in pgvector."
                        )
                        indexed_count += len(chunks)
                    except Exception as e:
                        logger.error(f"❌ Failed to index chunks in pgvector: {e}")

        logger.info(
            f"✨ Fandom Lore Pipeline finished. Processed {indexed_count} total ssemantic chunks."
        )


if __name__ == "__main__":
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(
        description="Acquiert le lore Fandom à grande échelle."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule l'indexation sans écrire dans pgvector.",
    )
    args = parser.parse_args()

    scraper = FandomLoreScraper(dry_run=args.dry_run)
    scraper.execute_pipeline()
