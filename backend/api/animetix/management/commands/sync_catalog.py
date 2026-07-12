import hashlib
import json
import os
import re

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from animetix.models import MediaItem

# Signatures of garbage "tags" left when an LLM enrichment step failed and stored
# its error message as a tag (e.g. "aucune unité de calcul d'IA n'est disponible
# (Ollama/HF)."). Matched case-insensitively as substrings; such entries are
# dropped from tags / micro_tags / traits at sync time.
_GARBAGE_TAG_SIGNATURES = (
    "aucune unité de calcul",
    "n'est disponible",
    "ollama/hf",
    "désolé",  # LLM refusal/error fragment ("Désolé, …") stored as a tag
    "traceback (most recent",
)
_TAG_FIELDS = ("tags", "micro_tags", "traits")

# The six JSON files this command has always synced, and how to resolve each
# item's external id. For anime/manga the id is the MAL id (`idMal` first):
# `anime_themes.json` is indexed by AniList id, `anime_episodes.json` by MAL id
# -- both must be resolvable from the stored row (see _prepare_item).
SYNC_CONFIGS = [
    {
        "file": "clean_root_animes.json",
        "type": "Anime",
        "id_fields": ["idMal", "mal_id", "id"],
    },
    {
        "file": "clean_root_mangas.json",
        "type": "Manga",
        "id_fields": ["idMal", "mal_id", "id"],
    },
    {
        "file": "filtered_characters.json",
        "type": "Character",
        "id_fields": ["id"],
    },
    {"file": "clean_root_movies.json", "type": "Movie", "id_fields": ["id"]},
    {"file": "clean_root_games.json", "type": "Game", "id_fields": ["id"]},
    {"file": "clean_root_actors.json", "type": "Actor", "id_fields": ["id"]},
]

# The fields this command ever writes to MediaItem. Used both to build the
# bulk_update() field list and to fingerprint a row (new vs. currently stored)
# so a routine re-sync over unchanged data can skip the write entirely.
_WRITE_FIELDS = (
    "title",
    "title_english",
    "title_native",
    "description",
    "image_url",
    "release_year",
    "rating",
    "popularity",
    "metadata",
)

# 500-1000 keeps a single INSERT/UPDATE statement (and the transaction wrapping
# it) short: one failure costs one batch, not the whole ~44 700-item run, and no
# transaction sits open for hours on the pooled Neon connection.
_BATCH_SIZE = 500


def popularity_of(item) -> float:
    """Anime/manga carry an int; characters carry {"favourites": n, "rank": n}."""
    value = item.get("popularity")
    if isinstance(value, dict):
        value = value.get("favourites")
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _clean_tag_list(values):
    """Drop LLM-error-message entries from a tag list; leave real tags untouched."""
    if not isinstance(values, list):
        return values
    cleaned = []
    for v in values:
        s = str(v).strip()
        if not s or any(sig in s.lower() for sig in _GARBAGE_TAG_SIGNATURES):
            continue
        cleaned.append(v)
    return cleaned


def _fingerprint(fields: dict) -> str:
    """Cheap content hash of exactly the fields this command writes.

    Used to compare a freshly-parsed item against what is already stored
    without ever diffing field-by-field: if the hash matches, the row is
    byte-identical to what the DB already holds and the write is skipped.
    """
    payload = {k: fields.get(k) for k in _WRITE_FIELDS}
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.blake2b(blob.encode("utf-8"), digest_size=16).hexdigest()


def _prepare_item(item: dict, config: dict):
    """Resolve an external id and build the MediaItem field values for one raw
    JSON record. Returns None if no external id can be resolved (unusable row).
    """
    ext_id = None
    for field in config["id_fields"]:
        if item.get(field):
            ext_id = str(item.get(field))
            break
    if not ext_id:
        return None

    # Mapping common fields
    title = item.get("title") or item.get("name")
    title_en = item.get("title_english") or item.get("title_en")
    title_nat = item.get("title_native") or item.get("title_jp")
    desc = (
        item.get("description") or item.get("synopsis") or item.get("biography") or ""
    )
    img = item.get("image") or item.get("image_url")
    year = item.get("year") or item.get("release_year")

    # Robust year parsing
    if isinstance(year, str):
        if year.isdigit():
            year = int(year)
        else:
            # Handle cases like "2021-2022" or "2021 (Spring)"
            match = re.search(r"\d{4}", year)
            year = int(match.group()) if match else None
    elif not isinstance(year, (int, float)):
        year = None

    rating = item.get("rating") or item.get("score")
    if isinstance(rating, str):
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            rating = None

    # Remove mapped fields from metadata to avoid redundancy
    metadata = item.copy()
    fields_to_pop = config["id_fields"] + [
        "title",
        "name",
        "title_english",
        "title_en",
        "title_native",
        "title_jp",
        "description",
        "synopsis",
        "biography",
        "image",
        "image_url",
        "year",
        "release_year",
        "rating",
        "score",
    ]
    for f in fields_to_pop:
        metadata.pop(f, None)

    # Les ids ne sont PAS des doublons : ce sont deux espaces de noms
    # distincts, et les données annexes n'y sont pas indexées pareil.
    # `anime_themes.json` est indexé par id AniList, `anime_episodes.json`
    # par id MAL. Les jeter ici rendait les 5 archétypes opening/épisode
    # du World Boss définitivement muets en production (silencieusement :
    # l'archétype rendait None et le moteur en tirait un autre).
    #
    # On les remet sous des clés stables, que `_to_dict` ré-expose via
    # `data.update(item.metadata)`. Surtout PAS sous `id` : cette clé est
    # déjà tenue par `external_id`, et l'écraser casserait
    # `id_to_full_data` (indexé sur `str(item["id"])`) et tous ses
    # consommateurs — Akinetix, Quiz Who, Covertest, le blind test.
    mal_id = item.get("idMal") or item.get("mal_id")
    if mal_id:
        metadata["idMal"] = str(mal_id)
    if item.get("id"):
        metadata["anilist_id"] = str(item["id"])

    # Strip garbage LLM-error tags so they never reach the DB.
    for tag_field in _TAG_FIELDS:
        if tag_field in metadata:
            metadata[tag_field] = _clean_tag_list(metadata[tag_field])

    fields = {
        "title": title or "Unknown",
        "title_english": title_en,
        "title_native": title_nat,
        "description": desc[:5000] if desc else "",
        "image_url": img,
        "release_year": int(year) if year else None,
        "rating": float(rating) if rating else None,
        "popularity": popularity_of(item),
        "metadata": metadata,
    }
    return ext_id, fields


class Command(BaseCommand):
    help = (
        "Bulk-syncs the processed JSON catalog files into MediaItem. Rewritten from "
        "one update_or_create() per item (a SELECT + INSERT/UPDATE round trip each, "
        "all inside one transaction) to batched bulk_create/bulk_update: against the "
        "remote Neon DB, the old command took 70+ minutes and never committed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Report what would be created/updated/skipped without writing "
            "to the database or touching the cache.",
        )
        parser.add_argument(
            "--media-type",
            choices=[c["type"] for c in SYNC_CONFIGS],
            default=None,
            help="Sync only this media type (e.g. Anime) instead of all six -- "
            "useful when only one catalog changed.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        media_type_filter = options.get("media_type")

        # Correctly find project root from backend/animetix/management/commands/sync_catalog.py
        # 1: commands, 2: management, 3: animetix, 4: backend, 5: project_root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
        data_processed_dir = os.path.join(project_root, "data", "processed")

        configs = SYNC_CONFIGS
        if media_type_filter:
            configs = [c for c in configs if c["type"] == media_type_filter]

        # ONE cheap query for every (media_type, external_id) -> pk currently in
        # the DB, across every type this run touches. Deliberately no `metadata`
        # here: it is the field that made the old per-item SELECT+INSERT/UPDATE
        # round trip expensive, and for 35k+ characters it can run into tens of
        # MB. This query only decides create-vs-update; the (much smaller,
        # per-batch) fetch below decides skip-vs-update.
        all_types = [c["type"] for c in configs]
        existing_pks = {t: {} for t in all_types}
        if all_types:
            for mt, ext_id, pk in MediaItem.objects.filter(
                media_type__in=all_types
            ).values_list("media_type", "external_id", "id"):
                existing_pks[mt][ext_id] = pk

        totals = {"created": 0, "updated": 0, "skipped": 0}
        touched_types = []

        for config in configs:
            path = os.path.join(data_processed_dir, config["file"])
            if not os.path.exists(path):
                self.stdout.write(self.style.WARNING(f"File not found: {path}"))
                continue

            media_type = config["type"]
            self.stdout.write(f"Syncing {media_type} from {config['file']}...")
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)

            prepared = []
            for item in items:
                result = _prepare_item(item, config)
                if result is None:
                    continue
                prepared.append(result)

            type_pks = existing_pks[media_type]
            created = updated = skipped = 0

            for start in range(0, len(prepared), _BATCH_SIZE):
                batch = prepared[start : start + _BATCH_SIZE]

                to_create = []
                to_check = []
                for ext_id, fields in batch:
                    if ext_id in type_pks:
                        to_check.append(ext_id)
                    else:
                        to_create.append((ext_id, fields))

                # Batch-scoped (<= _BATCH_SIZE rows), not one query for the
                # whole table: bounds how much metadata we ever materialize at
                # once while still needing only one query per batch.
                existing_rows = {}
                if to_check:
                    rows = MediaItem.objects.filter(
                        media_type=media_type, external_id__in=to_check
                    ).values("id", "external_id", *_WRITE_FIELDS)
                    for row in rows:
                        existing_rows[row["external_id"]] = row

                to_update = []
                for ext_id, fields in batch:
                    if ext_id not in type_pks:
                        continue
                    row = existing_rows.get(ext_id)
                    if row is None:
                        continue
                    if _fingerprint(fields) == _fingerprint(row):
                        skipped += 1
                        continue
                    to_update.append(
                        MediaItem(
                            pk=row["id"],
                            external_id=ext_id,
                            media_type=media_type,
                            **fields,
                        )
                    )

                if dry_run:
                    created += len(to_create)
                    updated += len(to_update)
                    continue

                # One transaction per batch: a failure costs this batch, not
                # the whole run, and no transaction stays open for hours.
                with transaction.atomic():
                    if to_create:
                        MediaItem.objects.bulk_create(
                            [
                                MediaItem(
                                    external_id=ext_id, media_type=media_type, **fields
                                )
                                for ext_id, fields in to_create
                            ],
                            batch_size=_BATCH_SIZE,
                            # A concurrent writer racing us on the same
                            # (external_id, media_type) must not blow up the run.
                            ignore_conflicts=True,
                        )
                    if to_update:
                        MediaItem.objects.bulk_update(
                            to_update, _WRITE_FIELDS, batch_size=_BATCH_SIZE
                        )

                created += len(to_create)
                updated += len(to_update)

            totals["created"] += created
            totals["updated"] += updated
            totals["skipped"] += skipped
            touched_types.append(media_type)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{media_type}: created={created} updated={updated} skipped={skipped}"
                )
            )

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}TOTAL: created={totals['created']} "
                f"updated={totals['updated']} skipped={totals['skipped']}"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run: nothing was written, the cache was not touched."
                )
            )
            return

        # Invalidate the Redis-level catalog cache for every type this run
        # touched: CatalogService caches each catalog under "catalog_{type}"
        # (TTL 1h). Without this, a sync is invisible to production for up to
        # an hour.
        for mt in touched_types:
            cache.delete(f"catalog_{mt}")

        self.stdout.write(
            self.style.WARNING(
                "Cleared the Redis catalog_{type} key for: "
                f"{', '.join(touched_types) if touched_types else '(none)'}. "
                "NOTE: CatalogService also keeps a per-process RAM cache "
                "(self._cached_catalogs) that never expires and CANNOT be "
                "reached from this command -- each Cloud Run instance will keep "
                "serving the old catalog from RAM until it restarts."
            )
        )
