import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from animetix.models import MangaCover


class Command(BaseCommand):
    help = "Pousse les covers de mangas du fichier JSON vers la table MangaCover dans Postgres"

    def handle(self, *args, **options):
        # Locate the JSON file
        from django.conf import settings

        repo_root = os.path.dirname(os.path.dirname(settings.BASE_DIR))
        json_path = os.path.join(repo_root, "data", "processed", "manga_covers.json")

        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Le fichier {json_path} n'existe pas."))
            return

        self.stdout.write(f"Lecture des données depuis {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.stdout.write(
            f"Chargement de {len(data)} mangas dans la base de données..."
        )

        # Load existing cover records to do smart delta sync or bulk creation
        existing_covers = {c.manga_id: c for c in MangaCover.objects.all()}

        to_create = []
        to_update = []

        for mid, info in data.items():
            manga_id = str(mid)
            title = info.get("title", "")
            mangadex_id = info.get("mangadex_id")
            covers = info.get("covers", {})
            title_english = info.get("title_english")
            title_native = info.get("title_native")
            synonyms = info.get("synonyms", [])
            author = info.get("author")

            existing = existing_covers.get(manga_id)
            if existing:
                # Check if changed to avoid redundant updates
                changed = (
                    existing.title != title
                    or existing.mangadex_id != mangadex_id
                    or existing.covers != covers
                    or existing.title_english != title_english
                    or existing.title_native != title_native
                    or existing.synonyms != synonyms
                    or existing.author != author
                )
                if changed:
                    existing.title = title
                    existing.mangadex_id = mangadex_id
                    existing.covers = covers
                    existing.title_english = title_english
                    existing.title_native = title_native
                    existing.synonyms = synonyms
                    existing.author = author
                    to_update.append(existing)
            else:
                to_create.append(
                    MangaCover(
                        manga_id=manga_id,
                        title=title,
                        mangadex_id=mangadex_id,
                        covers=covers,
                        title_english=title_english,
                        title_native=title_native,
                        synonyms=synonyms,
                        author=author,
                    )
                )

        # Execute bulk database operations
        with transaction.atomic():
            if to_create:
                MangaCover.objects.bulk_create(
                    to_create, batch_size=500, ignore_conflicts=True
                )
            if to_update:
                MangaCover.objects.bulk_update(
                    to_update,
                    [
                        "title",
                        "mangadex_id",
                        "covers",
                        "title_english",
                        "title_native",
                        "synonyms",
                        "author",
                    ],
                    batch_size=500,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronisation terminée : {len(to_create)} créés, {len(to_update)} mis à jour."
            )
        )
