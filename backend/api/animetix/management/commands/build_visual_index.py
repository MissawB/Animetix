"""Construit un index visuel depuis MediaItem.

La source est la BASE, pas les fichiers JSON : c'est elle qui sert le catalogue à
l'application. Indexer depuis les fichiers, c'est risquer d'écrire sous des
identifiants que personne n'interrogera — l'erreur qui a coûté la semaine.

Reprenable : on saute ce qui est déjà indexé. Une image morte (404, format
illisible, timeout) est journalisée et sautée ; elle ne fait jamais tomber le lot.
"""

import logging

from django.core.management.base import BaseCommand, CommandError

from animetix.models import MediaItem, VectorRecord

logger = logging.getLogger("animetix.visual_index")

BATCH = 100
TIMEOUT = 15


def _download(url: str):
    """Un seul point d'entrée réseau — moqué dans les tests."""
    from core.utils.security import safe_http_request  # noqa: E402

    response = safe_http_request("GET", url, timeout=TIMEOUT)
    if response.status_code != 200:
        return None
    return response.content


def _service():
    from animetix.containers import get_container  # noqa: E402

    return get_container().core.visual_index_service()


class Command(BaseCommand):
    help = "Construit l'index visuel d'une cible (work | character)."

    def add_arguments(self, parser):
        parser.add_argument("--target", required=True, choices=["work", "character"])
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--batch-size", type=int, default=BATCH)

    def handle(self, *args, **options):
        from core.domain.services.visual_index import TARGETS  # noqa: E402

        target = options["target"]
        if target not in TARGETS:
            raise CommandError(f"Cible inconnue : {target}")

        service = _service()
        spec = TARGETS[target]

        already = set(
            VectorRecord.objects.filter(collection_name=spec.collection).values_list(
                "item_id", flat=True
            )
        )
        # Le service peut exposer un ensemble déjà indexé (les tests s'en servent) ;
        # sinon on lit la collection.
        already |= set(getattr(service, "indexed_ids", set()) or set())

        rows = (
            MediaItem.objects.filter(media_type__in=spec.media_types)
            .exclude(image_url__isnull=True)
            .exclude(image_url="")
        )
        if options["limit"]:
            rows = rows.order_by("-popularity")[: options["limit"]]

        total, written, skipped = 0, 0, 0
        batch = []
        for row in rows.iterator(chunk_size=500):
            if str(row.external_id) in already:
                continue
            total += 1
            try:
                image_bytes = _download(row.image_url)
            except Exception as e:  # réseau : on saute, on ne perd pas le lot
                logger.warning("Téléchargement échoué (%s) : %s", row.title, e)
                image_bytes = None
            if not image_bytes:
                skipped += 1
                continue

            batch.append(
                {
                    "external_id": str(row.external_id),
                    "media_type": row.media_type,
                    "title": row.title,
                    "image": row.image_url,
                    "image_bytes": image_bytes,
                }
            )
            if len(batch) >= options["batch_size"]:
                written += service.index(target, batch)
                self.stdout.write(f"  {written} indexés ({skipped} sautés)...")
                batch = []

        if batch:
            written += service.index(target, batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"{target} : {written} vecteurs écrits dans {spec.collection}, "
                f"{skipped} images illisibles, {total} candidats."
            )
        )
