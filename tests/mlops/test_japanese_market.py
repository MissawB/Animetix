# -*- coding: utf-8 -*-
import sys
import os

# Configuration des chemins pour importer les modules du pipeline
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "pipeline", "mlops"))

from backend.pipeline.mlops.japanese_market_db import (  # noqa: E402
    JAPANESE_MANGA_PUBLISHERS,
    JAPANESE_ANIME_DISTRIBUTORS,
    JAPANESE_MARKET_RELATIONS,
    JAPANESE_VOICE_ACTORS,
)
from backend.pipeline.mlops.index_otaku_knowledge import OtakuKnowledgeIndexer  # noqa: E402
from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
    generate_japanese_market_profile_instructions,
    generate_japanese_market_relations_instructions,
)
from backend.pipeline.mlops.dpo_dataset_compiler import (  # noqa: E402
    PUBLISHERS_LIST,
    DISTRIBUTORS_LIST,
    RELATED_ENTITIES_MAP,
    JAPANESE_PUBLISHERS_SET,
    JAPANESE_DISTRIBUTORS_SET,
)


def test_japanese_market_db_size():
    """Vérifie que la base de données japonaise contient les bons effectifs."""
    assert len(JAPANESE_MANGA_PUBLISHERS) == 15, (
        "Doit contenir exactement 15 éditeurs japonais"
    )
    assert len(JAPANESE_ANIME_DISTRIBUTORS) == 10, (
        "Doit contenir exactement 10 diffuseurs japonais"
    )
    assert len(JAPANESE_MARKET_RELATIONS) == 40, (
        "Doit contenir exactement 40 relations japonaises"
    )
    assert len(JAPANESE_VOICE_ACTORS) >= 10, (
        "Doit réutiliser les seiyuu japonais (au moins 10)"
    )


def test_indexer_integration():
    """Vérifie que l'indexeur compile correctement les faits japonais."""
    indexer = OtakuKnowledgeIndexer(dry_run=True)
    facts = indexer.compile_all_facts()

    categories = [f["category"] for f in facts]
    assert "Japanese Manga Publishers" in categories
    assert "Japanese Anime Distributors (JP)" in categories

    jp_publishers_facts = [
        f for f in facts if f["category"] == "Japanese Manga Publishers"
    ]
    jp_distributors_facts = [
        f for f in facts if f["category"] == "Japanese Anime Distributors (JP)"
    ]

    assert len(jp_publishers_facts) == 15
    assert len(jp_distributors_facts) == 10


def test_sft_instruction_generators():
    """Vérifie la génération et le format des instructions SFT japonaises."""
    profile_instructions = generate_japanese_market_profile_instructions()
    relations_instructions = generate_japanese_market_relations_instructions()

    # 15 seiyuu * 15 + 15 éditeurs * 15 + 10 diffuseurs * 15 = 600
    assert len(profile_instructions) == 600, (
        f"Attendu 600 profils, obtenu {len(profile_instructions)}"
    )
    # 40 relations * 4 variations = 160
    assert len(relations_instructions) == 160, (
        f"Attendu 160 relations, obtenu {len(relations_instructions)}"
    )

    # Vérification du format
    for item in profile_instructions + relations_instructions:
        assert "instruction" in item
        assert "input" in item
        assert "output" in item
        assert item["input"] == ""
        assert len(item["instruction"]) > 0
        assert len(item["output"]) > 0


def test_dpo_corruption_regional_partition():
    """Vérifie que la partition régionale du compilateur DPO empêche les mélanges France/Japon."""
    # 1. Vérifier la présence dans les listes globales
    for jp_pub in JAPANESE_MANGA_PUBLISHERS.keys():
        assert jp_pub in PUBLISHERS_LIST

    for jp_dist in JAPANESE_ANIME_DISTRIBUTORS.keys():
        assert jp_dist in DISTRIBUTORS_LIST

    # 2. Vérifier que la substitution respecte la partition régionale (pas de mélange FR/JP)
    for jp_pub in JAPANESE_PUBLISHERS_SET:
        related = RELATED_ENTITIES_MAP.get(jp_pub, [])
        for item in related:
            assert item in JAPANESE_PUBLISHERS_SET, (
                f"Un éditeur japonais ({jp_pub}) ne peut être remplacé que par un autre éditeur japonais. Obtenu: {item}"
            )

    for jp_dist in JAPANESE_DISTRIBUTORS_SET:
        related = RELATED_ENTITIES_MAP.get(jp_dist, [])
        for item in related:
            assert item in JAPANESE_DISTRIBUTORS_SET, (
                f"Un diffuseur japonais ({jp_dist}) ne peut être remplacé que par un autre diffuseur japonais. Obtenu: {item}"
            )

    # Vérifier réciproquement pour le marché français
    french_pubs = [p for p in PUBLISHERS_LIST if p not in JAPANESE_PUBLISHERS_SET]
    for fr_pub in french_pubs:
        related = RELATED_ENTITIES_MAP.get(fr_pub, [])
        for item in related:
            assert item not in JAPANESE_PUBLISHERS_SET, (
                f"Un éditeur français ({fr_pub}) ne peut pas être remplacé par un éditeur japonais. Obtenu: {item}"
            )
