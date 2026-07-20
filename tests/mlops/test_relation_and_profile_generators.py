# -*- coding: utf-8 -*-
"""Tests des générateurs data-driven sous-couverts (reliquat audit 2026-07-19) :
relation_generators (32 %), market_profile_generators (58 %), otaku_generators (64 %).

Assertions sur le comportement réel : cardinalités relatives aux bases de
données (pas de nombres magiques), format Alpaca, et surtout GROUNDING — chaque
output doit contenir la réponse/les champs source, c'est la propriété qui a
cassé le premier fine-tune otaku (réponses templatées non ancrées).
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "pipeline", "mlops"))

import pytest  # noqa: E402
from pipeline.mlops import french_market_db  # noqa: E402
from pipeline.mlops.ft_dataset import (  # noqa: E402
    market_profile_generators,
    otaku_generators,
    relation_generators,
)
from pipeline.mlops.magazines_and_awards_db import (  # noqa: E402
    AWARDS_AND_MAGAZINES_RELATIONS,
)
from pipeline.mlops.otaku_concepts import OTAKU_VOCABULARY  # noqa: E402
from pipeline.mlops.songs_and_seiyuu_db import (  # noqa: E402
    SONGS_AND_SEIYUU_RELATIONS,
)
from pipeline.mlops.transmedia_db import TRANSMEDIA_RELATIONS  # noqa: E402
from pipeline.mlops.volumes_and_episodes_db import (  # noqa: E402
    VOLUMES_AND_EPISODES_DATA,
)


def _assert_alpaca_format(items):
    for item in items:
        assert set(item.keys()) >= {"instruction", "input", "output"}
        assert item["input"] == ""
        assert len(item["instruction"]) > 0
        assert len(item["output"]) > 0


# --- relation_generators --------------------------------------------------


@pytest.mark.parametrize(
    "generator, db",
    [
        (
            relation_generators.generate_transmedia_instructions,
            TRANSMEDIA_RELATIONS,
        ),
        (
            relation_generators.generate_awards_and_magazines_instructions,
            AWARDS_AND_MAGAZINES_RELATIONS,
        ),
        (
            relation_generators.generate_songs_and_seiyuu_instructions,
            SONGS_AND_SEIYUU_RELATIONS,
        ),
        (
            relation_generators.generate_french_market_relations_instructions,
            french_market_db.FRENCH_MARKET_RELATIONS,
        ),
    ],
)
def test_relation_generators_four_grounded_variations_per_relation(generator, db):
    items = generator()

    assert len(items) == 4 * len(db)
    _assert_alpaca_format(items)

    # Grounding : chacune des 4 variations d'une relation contient sa réponse
    # source (les variations préfixent mais n'altèrent jamais la réponse).
    for i, relation in enumerate(db):
        for item in items[4 * i : 4 * i + 4]:
            assert relation["answer"] in item["output"]

    # La variation « expert » (3e) abaisse la première lettre de la question.
    q0 = db[0]["question"]
    assert q0[0].lower() + q0[1:] in items[2]["instruction"]


def test_volumes_and_episodes_instructions_grounded():
    items = relation_generators.generate_volumes_and_episodes_instructions()

    assert len(items) == 4 * len(VOLUMES_AND_EPISODES_DATA)
    _assert_alpaca_format(items)

    # Grounding : les 4 variations d'un titre portent le titre et ses données.
    title, data = next(iter(VOLUMES_AND_EPISODES_DATA.items()))
    first_four = items[:4]
    for item in first_four:
        assert title in item["instruction"]
        assert data["status"] in item["output"]
    # Le récapitulatif complet (3e variation) porte tomes ET épisodes.
    assert data["manga_volumes"] in first_four[2]["output"]
    assert data["anime_episodes"] in first_four[2]["output"]


# --- market_profile_generators (côté français) -----------------------------


def test_french_market_profiles_grounded_and_sized():
    items = market_profile_generators.generate_french_market_profile_instructions()

    expected = 15 * (
        len(french_market_db.FRENCH_VOICE_ACTORS)
        + len(french_market_db.FRENCH_MANGA_PUBLISHERS)
        + len(french_market_db.FRENCH_ANIME_DISTRIBUTORS)
    )
    assert len(items) == expected
    _assert_alpaca_format(items)

    # Grounding par section : les 15 variations d'une entité mentionnent
    # l'entité, et sa définition source apparaît dans au moins une d'elles.
    for db, offset in [
        (french_market_db.FRENCH_VOICE_ACTORS, 0),
        (
            french_market_db.FRENCH_MANGA_PUBLISHERS,
            15 * len(french_market_db.FRENCH_VOICE_ACTORS),
        ),
        (
            french_market_db.FRENCH_ANIME_DISTRIBUTORS,
            15
            * (
                len(french_market_db.FRENCH_VOICE_ACTORS)
                + len(french_market_db.FRENCH_MANGA_PUBLISHERS)
            ),
        ),
    ]:
        entity, data = next(iter(db.items()))
        block = items[offset : offset + 15]
        assert all(entity in item["instruction"] for item in block)
        assert any(data["definition"] in item["output"] for item in block)


# --- otaku_generators -------------------------------------------------------


def test_otaku_meta_instructions_french_only_without_client():
    from pipeline.mlops.creators_db import CREATORS_AND_STUDIOS

    items = otaku_generators.generate_otaku_meta_instructions(client=None)

    expected = 15 * len(OTAKU_VOCABULARY) + 15 * len(CREATORS_AND_STUDIOS) + 12
    assert len(items) == expected
    _assert_alpaca_format(items)
    # Sans client, aucune bascule EN : tout est étiqueté Français.
    assert all(item["language"] == "Français" for item in items)

    # Les 12 comparaisons croisées ferment la liste, ancrées sur le vocabulaire.
    comparisons = items[-12:]
    for item in comparisons:
        assert "différence fondamentale" in item["instruction"]
    assert OTAKU_VOCABULARY["Tsundere"]["examples"] in comparisons[0]["output"]
    assert OTAKU_VOCABULARY["Yandere"]["examples"] in comparisons[0]["output"]


def test_otaku_meta_instructions_alternates_english_with_client(monkeypatch):
    # On ne teste pas la traduction Gemini ici (couverte dans test_paraphrase) :
    # on vérifie que la branche client bascule bien un concept sur deux en EN
    # et injecte les champs traduits dans les outputs.
    monkeypatch.setattr(
        otaku_generators,
        "translate_to_english_via_gemini",
        lambda text, client: f"EN::{text}",
    )

    items = otaku_generators.generate_otaku_meta_instructions(client=object())

    languages = {item["language"] for item in items}
    assert languages == {"Français", "English"}

    english = [item for item in items if item["language"] == "English"]
    assert english, "le client doit activer la branche anglaise"
    assert all("EN::" in item["output"] for item in english)
    # Alternance : le 2e concept (idx 1) est anglais, le 1er reste français.
    assert items[0]["language"] == "Français"
    assert items[15]["language"] == "English"
