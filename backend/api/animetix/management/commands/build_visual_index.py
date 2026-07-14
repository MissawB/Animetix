"""Construit un index visuel depuis MediaItem.

La source est la BASE, pas les fichiers JSON : c'est elle qui sert le catalogue à
l'application. Indexer depuis les fichiers, c'est risquer d'écrire sous des
identifiants que personne n'interrogera — l'erreur qui a coûté la semaine.

Reprenable : on saute ce qui est déjà DANS la collection (`VectorRecord`), clé
par clé. Une image morte (404, format illisible, timeout) est journalisée et
sautée ; elle ne fait jamais tomber le lot.

La clé d'un vecteur est `media_type:external_id` (`vector_key`) — jamais
l'external_id nu, qui n'est unique que par type de média alors que la cible
`work` verse quatre types dans une seule collection. Écrivain et lecteur
appellent LA MÊME fonction : c'est la seule garantie qu'ils ne divergeront pas.

Une écriture qui échoue lève (CommandError) : mieux vaut s'arrêter — la reprise
ne coûtera que ce qui reste — qu'annoncer en vert des vecteurs qui n'existent pas.
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

    def _write(self, service, target, batch):
        """Le seul endroit qui écrit. Un échec s'arrête ici, il ne se déguise pas
        en succès : `service.index` écrit en mode strict, donc ce qu'il rend est
        ce qui est VRAIMENT dans la collection."""
        try:
            return service.index(target, batch)
        except Exception as e:
            raise CommandError(
                f"Écriture du lot échouée dans {target} ({len(batch)} vecteurs "
                f"perdus, le lot entier a été annulé) : {e}. Rien n'a été annoncé "
                "comme écrit. Relancer la commande : elle reprendra où elle s'est "
                "arrêtée."
            ) from e

    def handle(self, *args, **options):
        from core.domain.services.visual_index import TARGETS, vector_key  # noqa: E402

        target = options["target"]
        if target not in TARGETS:
            raise CommandError(f"Cible inconnue : {target}")

        service = _service()
        spec = TARGETS[target]

        # La reprise se lit dans la collection elle-même, la seule source qui sache
        # ce qui a réellement été écrit — et elle se compare en CLÉS COMPOSITES.
        # Comparer des external_id nus ferait sauter des œuvres jamais indexées (un
        # « 1 » de film prendrait le « 1 » d'un anime pour lui) et rendrait la
        # reprise fausse dans les deux sens.
        already = set(
            VectorRecord.objects.filter(collection_name=spec.collection).values_list(
                "item_id", flat=True
            )
        )

        rows = (
            MediaItem.objects.filter(media_type__in=spec.media_types)
            .exclude(image_url__isnull=True)
            .exclude(image_url="")
        )
        limit = options["limit"]
        # L'ordre par popularité n'a de sens QUE pour choisir quels `limit`
        # candidats indexer en premier -- sans limite, tout finit par être
        # indexé et l'ordre est indifférent.
        if limit:
            rows = rows.order_by("-popularity")

        total, written, skipped, encode_failed = 0, 0, 0, 0
        batch = []

        def _flush(batch):
            """Écrit le lot et compte SÉPARÉMENT ce qui n'a pas été écrit à
            cause d'un échec d'ENCODAGE (par opposition au téléchargement,
            compté dans `skipped` avant même d'atteindre le service).

            `VisualIndexService.index` avale toute exception d'encodage par
            image (`encode_image`) et saute juste l'item -- une décision
            correcte pour survivre à UNE jaquette illisible, mais qui rend
            silencieux le cas où TOUT échoue (Hub down, `open_clip` absent,
            Brain injoignable) : le nombre écrit tombe à 0 sans qu'aucune
            exception ne remonte ici. `len(batch) - batch_written` est
            précisément ce delta -- la seule donnée qui existe encore une fois
            que `index()` a rendu son compte.
            """
            batch_written = self._write(service, target, batch)
            return batch_written, len(batch) - batch_written

        for row in rows.iterator(chunk_size=500):
            if vector_key(row.media_type, row.external_id) in already:
                continue
            # `--limit` compte des candidats À INDEXER, jamais des lignes SQL
            # brutes : appliqué comme un `[:limit]` avant ce filtre, une
            # relance sur un catalogue déjà partiellement indexé slicait les
            # `limit` lignes les PLUS populaires -- précisément celles qu'un
            # premier passage avait déjà indexées -- et n'en soumettait plus
            # aucune de neuve à `service.index`. Compter ici, après
            # l'exclusion, garantit que `limit` NOUVEAUX candidats sont
            # traités, quel que soit ce qui est déjà dans `already`.
            if limit and total >= limit:
                break
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
                batch_written, batch_encode_failed = _flush(batch)
                written += batch_written
                encode_failed += batch_encode_failed
                self.stdout.write(f"  {written} indexés ({skipped} sautés)...")
                batch = []

        if batch:
            batch_written, batch_encode_failed = _flush(batch)
            written += batch_written
            encode_failed += batch_encode_failed

        # Un total encodeur en panne (Hub down, `open_clip` absent, Brain
        # injoignable) ne lève rien dans `index()` -- chaque image est juste
        # "sautée" une par une. Sans ce garde-fou, `total` candidats et
        # `written == 0` s'annonçaient quand même en vert : 9200 candidats,
        # 0 vecteurs écrits, "SUCCESS". Il y avait des candidats et rien n'a
        # été écrit : ce n'est jamais un succès, silencieux ou non.
        if total and not written:
            raise CommandError(
                f"{target} : {total} candidats, 0 vecteur écrit ({encode_failed} "
                f"échecs d'encodage, {skipped} images illisibles). L'encodeur "
                "semble totalement en panne -- rien n'a été annoncé comme "
                "écrit. Relancer la commande une fois le moteur d'inférence "
                "rétabli : elle reprendra où elle s'est arrêtée."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{target} : {written} vecteurs écrits dans {spec.collection}, "
                f"{encode_failed} échecs d'encodage, {skipped} images "
                f"illisibles, {total} candidats."
            )
        )
