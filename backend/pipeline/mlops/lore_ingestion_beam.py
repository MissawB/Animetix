import os
import re
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from typing import Dict, List

logger = logging.getLogger("animetix.pipeline.beam")


class ScrapeAndCleanDoFn(beam.DoFn):
    def process(self, element: Dict) -> List[Dict]:
        url = element.get("url")
        franchise = element.get("franchise")
        if not url:
            return []

        logger.info(f"Beam: Scraping URL {url} for franchise {franchise}")
        try:
            from core.utils.security import safe_http_request  # noqa: E402

            try:
                from bs4 import BeautifulSoup  # noqa: E402
            except ImportError:
                BeautifulSoup = None

            headers = {"User-Agent": "Mozilla/5.0"}
            response = safe_http_request("GET", url, headers=headers, timeout=10)
            html = response.content

            if BeautifulSoup:
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style", "noscript", "iframe", "aside"]):
                    tag.decompose()
                content_div = (
                    soup.find(id="mw-content-text")
                    or soup.find(class_="mw-parser-output")
                    or soup
                )
                text = content_div.get_text(separator=" ")
            else:
                html_str = html.decode("utf-8", errors="ignore")
                html_str = re.sub(
                    r"<(script|style|noscript|iframe|aside)[^>]*>.*?</\1>",
                    "",
                    html_str,
                    flags=re.DOTALL,
                )
                text = re.sub(r"<[^>]+>", " ", html_str)

            clean_text = re.sub(r"\s+", " ", text).strip()[:8000]

            yield {"url": url, "franchise": franchise, "text": clean_text}
        except Exception as e:
            logger.error(f"Beam error scraping {url}: {e}")
            return []


class ChunkTextDoFn(beam.DoFn):
    def process(self, element: Dict) -> List[Dict]:
        text = element["text"]
        url = element["url"]
        franchise = element["franchise"]

        sentence_end = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_end.split(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if current_length + len(sentence) > 400 and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        yield {"url": url, "franchise": franchise, "chunks": chunks}


class IngestionOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--pubsub_subscription", type=str, help="Pub/sub subscription path"
        )
        parser.add_argument("--database_url", type=str, help="Database connection URL")
        parser.add_argument(
            "--django_env", type=str, default="production", help="Django environment"
        )


class GenerateEmbeddingsDoFn(beam.DoFn):
    def __init__(self, database_url=None, django_env=None):
        self.database_url = database_url
        self.django_env = django_env
        super().__init__()

    def setup(self):
        if self.database_url:
            os.environ["DATABASE_URL"] = self.database_url
        if self.django_env:
            os.environ["DJANGO_ENV"] = self.django_env
        import django  # noqa: E402

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
        try:
            django.setup()
            from animetix.containers import get_container  # noqa: E402

            self.container = get_container()
        except Exception as e:
            logger.warning(f"Django setup warning in Beam worker: {e}")
            self.container = None

    def process(self, element: Dict) -> List[Dict]:
        chunks = element["chunks"]
        url = element["url"]
        franchise = element["franchise"]

        results = []
        embedding_fn = None
        if self.container:
            try:
                repo = self.container.persistence.repository()
                embedding_fn = repo.chroma.embedding_fn
            except Exception as e:
                logger.error(f"Failed to get embedding function: {e}")

        for idx, chunk in enumerate(chunks):
            context_header = (
                f"[Source: Fandom Lore | Franchise: {franchise.title()} | URL: {url}] "
            )
            chunk_text = context_header + chunk

            # Embed chunk
            if embedding_fn:
                try:
                    vector = list(embedding_fn([chunk_text])[0])
                except Exception as e:
                    logger.error(f"Embedding generation error: {e}")
                    vector = [0.0] * 768
            else:
                # Local mock vector dimension 768
                vector = [0.1 * (idx % 10)] * 768

            results.append(
                {
                    "doc_id": f"beam_lore_{franchise}_{hash(url)}_{idx}",
                    "chunk_text": chunk_text,
                    "vector": vector,
                    "metadata": {
                        "title": f"Lore {franchise.title()}",
                        "description": chunk_text,
                        "source": "Beam Real-Time Ingestion",
                        "franchise": franchise,
                    },
                }
            )

        yield {"url": url, "franchise": franchise, "items": results}


class WriteToVectorDBDoFn(beam.DoFn):
    def __init__(self, database_url=None, django_env=None):
        self.database_url = database_url
        self.django_env = django_env
        super().__init__()

    def setup(self):
        if self.database_url:
            os.environ["DATABASE_URL"] = self.database_url
        if self.django_env:
            os.environ["DJANGO_ENV"] = self.django_env
        import django  # noqa: E402

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
        try:
            django.setup()
            from animetix.containers import get_container  # noqa: E402

            self.container = get_container()
        except Exception as e:
            logger.warning(f"Django setup warning in Beam worker: {e}")
            self.container = None

    def process(self, element: Dict) -> List[Dict]:
        items = element["items"]
        if not items:
            return []

        if self.container:
            try:
                repo = self.container.persistence.repository()
                collection_name = repo.chroma.coll_names.get("Anime", "anime_thematic")

                ids = [x["doc_id"] for x in items]
                embeddings = [x["vector"] for x in items]
                metadatas = [x["metadata"] for x in items]

                repo.chroma.upsert_items(collection_name, ids, embeddings, metadatas)
                logger.info(
                    f"Beam: Successfully upserted {len(items)} items to Vector DB"
                )
            except Exception as e:
                logger.error(f"Beam: Error upserting items to Vector DB: {e}")
        else:
            logger.info(f"Beam Simulation: Upserting {len(items)} items to Vector DB")

        yield element


def run_pipeline(argv=None, test_input=None):
    pipeline_options = PipelineOptions(argv)

    with beam.Pipeline(options=pipeline_options) as p:
        if test_input is not None:
            # Read from static test inputs (DirectRunner Testing)
            raw_input = p | "CreateMockInput" >> beam.Create(test_input)
            db_url = None
            dj_env = None
        else:
            options = pipeline_options.view_as(IngestionOptions)
            subscription_path = options.pubsub_subscription
            db_url = options.database_url
            dj_env = options.django_env
            if not subscription_path:
                raise ValueError("Missing required parameter: --pubsub_subscription")
            raw_input = (
                p
                | "ReadFromPubSub"
                >> beam.io.ReadFromPubSub(subscription=subscription_path)
                | "DecodeMessage"
                >> beam.Map(lambda bytes_data: json.loads(bytes_data.decode("utf-8")))
            )

        (
            raw_input
            | "ScrapeAndClean" >> beam.ParDo(ScrapeAndCleanDoFn())
            | "ChunkText" >> beam.ParDo(ChunkTextDoFn())
            | "GenerateEmbeddings"
            >> beam.ParDo(
                GenerateEmbeddingsDoFn(database_url=db_url, django_env=dj_env)
            )
            | "WriteToVectorDB"
            >> beam.ParDo(WriteToVectorDBDoFn(database_url=db_url, django_env=dj_env))
        )


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    import sys  # noqa: E402

    run_pipeline(sys.argv[1:])
