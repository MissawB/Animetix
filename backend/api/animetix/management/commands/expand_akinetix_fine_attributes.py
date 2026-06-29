"""Expand Akinetix "fine" character traits from catalogue tags/genres.

The fine traits (data/processed/akinetix_attributes.json) were 6 hand-curated
booleans over only 272 works, so character-style questions ("Ton personnage
utilise la magie ?") almost never fired. This derives a broader, character-
framed set from the now-rich tags/genres and MERGES it with the existing file
(hand-curated entries that can't be derived, e.g. a_des_cheveux_blonds, are
preserved).

Keys are snake_case French so the formatter renders them naturally
("utilise_la_magie" -> "Ton personnage utilise la magie ?"). Values stored as
True only (absence = false), matching the existing format. Keyed by the work's
external_id (AniList id), like the catalogue.

Usage:
    python manage.py expand_akinetix_fine_attributes
    python manage.py expand_akinetix_fine_attributes --media-type Anime
"""

import json
import os

from core.domain.services.akinetix.question_formatter import is_valid_micro_tag
from django.conf import settings
from django.core.management.base import BaseCommand

from animetix.models import MediaItem

# trait key (snake_case FR) -> trigger tags/genres (lowercased, matched against
# the item's genres + valid tags). Chosen to read as character/narrative traits.
TRAIT_RULES = {
    "utilise_la_magie": {"magic", "witch", "mahou shoujo", "magie"},
    "possede_des_super_pouvoirs": {"super power", "superhero"},
    "est_un_lyceen": {"school", "school club"},
    "porte_une_epee": {"swordplay"},
    "pratique_un_art_martial": {"martial arts"},
    "pilote_un_mecha": {"mecha"},
    "est_une_fille": {"female protagonist"},
    "est_un_garcon": {"male protagonist"},
    "evolue_dans_un_autre_monde": {"isekai"},
    "affronte_des_demons": {"demons", "devil"},
    "est_un_vampire": {"vampire"},
}


class Command(BaseCommand):
    help = "Derive & merge Akinetix fine character traits from tags/genres."

    def add_arguments(self, parser):
        parser.add_argument("--media-type", default="Anime")

    def handle(self, *args, **opts):
        path = os.path.join(
            settings.PROJECT_ROOT, "data", "processed", "akinetix_attributes.json"
        )
        existing = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        before_entries = len(existing)
        before_keys = {k for v in existing.values() for k in v}

        items = MediaItem.objects.filter(media_type=opts["media_type"])
        derived = added = 0
        for it in items:
            meta = it.metadata or {}
            signal = {
                s.lower()
                for s in (meta.get("genres") or [])
                + [t for t in (meta.get("tags") or []) if is_valid_micro_tag(t)]
            }
            if not signal:
                continue
            traits = {
                key: True for key, triggers in TRAIT_RULES.items() if signal & triggers
            }
            if not traits:
                continue
            key = str(it.external_id)
            merged = {**existing.get(key, {}), **traits}
            if merged != existing.get(key):
                added += len(set(traits) - set(existing.get(key, {})))
                existing[key] = merged
                derived += 1

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=0)

        after_keys = {k for v in existing.values() for k in v}
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. entries {before_entries} -> {len(existing)}; "
                f"distinct traits {len(before_keys)} -> {len(after_keys)}; "
                f"{derived} works updated (+{added} trait flags)."
            )
        )
