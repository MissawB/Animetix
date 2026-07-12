# tests/core/test_world_boss_db_catalogue.py
"""Le catalogue tel qu'il arrive EN PRODUCTION : de la base, pas du JSON.

Toutes les autres fixtures de la suite ont la forme du fichier JSON. C'est
précisément cet angle mort qui a laissé passer deux bugs critiques :

  * la base expose le nom d'un personnage sous ``title`` — jamais sous ``name`` —
    et quatre archétypes lisaient ``c["name"]`` : KeyError → 500 en plein raid ;
  * la base expose ``id`` = l'id MAL et n'a NI ``idMal`` NI l'id AniList, si bien
    que les openings (indexés par id AniList) et les épisodes (indexés par id MAL)
    ne résolvaient plus rien : 5 archétypes muets, en silence.

Ici, œuvres et personnages traversent le vrai ``DjangoRepositoryAdapter._to_dict``.
"""

import logging
import random
from unittest.mock import MagicMock

import pytest
from adapters.persistence.django_repository_adapter import DjangoRepositoryAdapter
from animetix.models import MediaItem
from core.domain.services.world_boss import (  # noqa: F401  (enregistre les archétypes)
    archetypes_core,
    archetypes_relational,
)
from core.domain.services.world_boss.context import QuizContext
from core.domain.services.world_boss.registry import ARCHETYPES
from core.domain.services.world_boss.service import WorldBossQuizService

from tests.core.test_world_boss_archetypes_core import ANIMES

# Les colonnes que `sync_catalog` fait remonter en champs propres : elles sont
# retirées de `metadata` au moment du sync (cf. `fields_to_pop`). `popularity`,
# elle, n'est PAS retirée — d'où le dict {"favourites": ..., "rank": ...} qui
# survit dans metadata pour les personnages, et dont dépend `_rank`.
_MAPPED = {
    "id",
    "idMal",
    "mal_id",
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
}

CHARACTERS = [
    {
        "id": 1001,
        "name": "Tanjiro Kamado",
        "origin": "Kimetsu no Yaiba",
        "popularity": {"favourites": 30000, "rank": 3},
        "entities": {"organizations": ["Demon Slayer Corps"]},
    },
    {
        "id": 1002,
        "name": "Zenitsu Agatsuma",
        "origin": "Kimetsu no Yaiba",
        "popularity": {"favourites": 200, "rank": 900},
        "entities": {"organizations": ["Demon Slayer Corps"]},
    },
    {
        "id": 1003,
        "name": "Spike Spiegel",
        "origin": "Cowboy Bebop",
        "popularity": {"favourites": 25000, "rank": 8},
        "entities": {"organizations": ["Bebop Crew"]},
    },
    {
        "id": 1004,
        "name": "Ed",
        "origin": "Cowboy Bebop",
        "popularity": {"favourites": 150, "rank": 950},
        "entities": {"organizations": ["Bebop Crew"]},
    },
    {
        "id": 1005,
        "name": "Johan Liebert",
        "origin": "Monster",
        "popularity": {"favourites": 20000, "rank": 12},
        "entities": {"organizations": ["511 Kinderheim"]},
    },
    {
        "id": 1006,
        "name": "Satoru Gojo",
        "origin": "Jujutsu Kaisen",
        "popularity": {"favourites": 40000, "rank": 1},
        "entities": {"organizations": ["Tokyo Jujutsu High"]},
    },
    {
        "id": 1007,
        "name": "Nobara Kugisaki",
        "origin": "Jujutsu Kaisen",
        "popularity": {"favourites": 300, "rank": 700},
        "entities": {"organizations": ["Tokyo Jujutsu High"]},
    },
    {
        # `secondary_character` needs a work with >= 3 known characters (the
        # rest of this fixture tops out at 2 per work): give Jujutsu Kaisen a
        # third castmate, less loved than both Gojo and Nobara.
        "id": 1008,
        "name": "Yuji Itadori",
        "origin": "Jujutsu Kaisen",
        "popularity": {"favourites": 250, "rank": 2},
        "entities": {"organizations": ["Tokyo Jujutsu High"]},
    },
]

# Les openings sont livrés par AnimeThemes.moe : la clé est l'id AniList, et
# l'entrée porte l'id MAL à l'intérieur.
THEMES = {
    str(anime["id"]): {
        "title": anime["title"],
        "mal_id": anime["idMal"],
        "themes": [
            {
                "type": "OP",
                "song_title": f"OP de {anime['title']}",
                "artists": [f"Groupe {anime['id']}"],
                "entries": [{"version": 1, "episodes": f"1-{anime['id'] + 10}"}],
            }
        ],
    }
    for anime in ANIMES
}

# Les épisodes viennent de Kitsu : la clé est l'id MAL.
EPISODES = {
    str(anime["idMal"]): [
        {
            "number": 1,
            "title": f"Le premier épisode de {anime['title']}",
            "synopsis": f"Un récit qui commence pour {anime['title']}.",
        }
    ]
    for anime in ANIMES
}


def _row(item: dict, media_type: str) -> MediaItem:
    """Une ligne MediaItem telle que `sync_catalog` l'écrit aujourd'hui.

    Les ids sont retirés de metadata et `external_id` porte l'id MAL pour un
    anime, l'id AniList pour un personnage : c'est l'état RÉEL de la base de prod
    (déjà synchronisée), donc le catalogue que le quiz doit savoir servir même
    sans re-sync.
    """
    metadata = {k: v for k, v in item.items() if k not in _MAPPED}
    popularity = item.get("popularity")
    if isinstance(popularity, dict):
        popularity = popularity.get("favourites")
    return MediaItem(
        external_id=str(item.get("idMal") or item["id"]),
        media_type=media_type,
        title=item.get("title") or item.get("name") or "Unknown",
        image_url=item.get("image"),
        release_year=item.get("year"),
        popularity=float(popularity or 0),
        metadata=metadata,
    )


def _db_catalogue():
    adapter = DjangoRepositoryAdapter()
    animes = [adapter._to_dict(_row(a, "Anime")) for a in ANIMES]
    characters = [adapter._to_dict(_row(c, "Character")) for c in CHARACTERS]
    return animes, characters


def _service(themes=None, episodes=None) -> WorldBossQuizService:
    animes, characters = _db_catalogue()
    catalog = MagicMock()
    catalog.load_data.side_effect = lambda media_type: {
        "Anime": {"db": animes},
        "Character": {"db": characters},
    }.get(media_type)
    catalog.repository.load_themes.return_value = themes if themes is not None else {}
    catalog.get_anime_episodes.return_value = (
        episodes if episodes is not None else EPISODES
    )
    return WorldBossQuizService(catalog_service=catalog)


class _FirstDrawIs(random.Random):
    """Un hasard normal — mais dont le PREMIER `choice` d'archétype est truqué."""

    def __init__(self, first, seed: int = 0):
        super().__init__(seed)
        self._first = first

    def choice(self, seq):
        if self._first is not None and any(item is self._first for item in seq):
            first, self._first = self._first, None
            return first
        return super().choice(seq)


def _context() -> QuizContext:
    """Le contexte que le moteur fabrique vraiment — pas un dict écrit à la main.
    Palier 12 + Brisage de Limiteur : le pool, c'est tout le catalogue."""
    return _service(themes=THEMES, episodes=EPISODES)._context(
        tier=12, limiter_break=True
    )


def test_the_db_catalogue_really_is_the_shape_we_think_it_is():
    """Le garde-fou du garde-fou : si `_to_dict` changeait de forme, ces tests
    protégeraient un fantôme."""
    animes, characters = _db_catalogue()

    assert "name" not in characters[0]  # LE piège : le nom est sous `title`
    assert characters[0]["title"] == "Tanjiro Kamado"
    assert characters[0]["origin"] == "Kimetsu no Yaiba"
    # Et l'id du catalogue est l'id MAL, pas l'id AniList des openings.
    assert animes[0]["id"] == str(ANIMES[0]["idMal"])


@pytest.mark.parametrize("name", sorted(ARCHETYPES))
def test_no_archetype_ever_raises_on_a_db_shaped_catalogue(name):
    """Un archétype décline (None) ou compose une question. Il ne LÈVE PAS.

    `build_question` ne gardait pas `.build()` et la vue ne rattrape que
    `GameLogicError` : un KeyError devenait un 500 en pleine montée.
    """
    ctx = _context()

    for seed in range(40):
        question = ARCHETYPES[name].build(ctx, random.Random(seed))
        if question is None:
            continue
        assert len(question.options) == 4
        assert 0 <= question.correct_index < 4
        assert question.prompt


@pytest.mark.parametrize(
    "name",
    [
        "character_origin",
        "same_work_character",
        "secondary_character",
        "character_sheet",
    ],
)
def test_the_character_archetypes_still_fire_when_the_name_is_a_title(name):
    ctx = _context()

    questions = [ARCHETYPES[name].build(ctx, random.Random(s)) for s in range(40)]
    questions = [q for q in questions if q is not None]

    assert questions, f"{name} n'a jamais rien produit sur un catalogue de base"
    every_name = {c["name"] for c in CHARACTERS}
    for question in questions:
        # L'énoncé et la réponse doivent citer un vrai nom, pas une chaîne vide.
        assert any(n in question.prompt for n in every_name) or any(
            option in every_name for option in question.options
        )
        assert all(option.strip() for option in question.options)


@pytest.mark.parametrize(
    "name",
    [
        "opening_to_work",
        "opening_artist",
        "opening_range",
        "episode_title",
        "episode_synopsis",
    ],
)
def test_openings_and_episodes_resolve_whichever_id_the_catalogue_carries(name):
    """Les 5 archétypes muets. Le catalogue de base ne porte QUE l'id MAL : les
    openings (indexés AniList) doivent quand même se laisser retrouver."""
    ctx = _context()

    questions = [ARCHETYPES[name].build(ctx, random.Random(s)) for s in range(40)]

    assert any(
        q is not None for q in questions
    ), f"{name} n'a jamais tiré : les identifiants ne se rejoignent pas"


class _Sink(logging.Handler):
    """caplog n'entend rien : le logger applicatif ne propage pas jusqu'à la
    racine (config Django). On écoute donc le logger du service directement."""

    def __init__(self):
        super().__init__(level=logging.NOTSET)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_build_question_survives_an_archetype_that_raises(monkeypatch):
    """Un archétype qui explose est un BUG — mais il ne doit pas coûter la partie
    au joueur : on le crie dans les logs, et on retire."""
    from core.domain.services.world_boss import registry, service as service_mod

    def _boom(ctx, rng):
        raise KeyError("name")

    exploding = registry.Archetype(name="year", bands=frozenset({"A"}), build=_boom)
    monkeypatch.setitem(registry.ARCHETYPES, "year", exploding)

    sink = _Sink()
    service_mod.logger.addHandler(sink)
    monkeypatch.setattr(service_mod.logger, "level", logging.DEBUG)
    try:
        # Le premier tirage tombe sur l'archétype qui explose — sinon le test
        # passerait par chance, sans jamais exercer le garde-fou.
        question = _service(themes=THEMES).build_question(
            tier=1, rng=_FirstDrawIs(exploding)
        )
    finally:
        service_mod.logger.removeHandler(sink)

    assert question is not None
    assert question.archetype != "year"
    shouted = [r for r in sink.records if r.levelno >= logging.ERROR]
    assert shouted, "un archétype qui lève doit être signalé, pas avalé en silence"
    assert shouted[0].exc_info, "la trace du bug doit rester dans les logs"
