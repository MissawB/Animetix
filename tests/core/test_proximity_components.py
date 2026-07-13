"""The four components of the proximity signal.

The embedding this replaces put Kimetsu no Yaiba closer to Death Note (0.671)
than Monster is (0.654), on a catalogue whose random-pair baseline is 0.583.
These tests pin the properties that make the new signal honest: rarity beats
frequency, the recommendation graph carries the human judgement, and a bonus
can never carry a score on its own.
"""

import pytest
from core.domain.services.proximity.components import (
    BONUS_CAP,
    W_CO_RECO,
    W_DIRECT,
    W_TAGS,
    build_index,
    co_reco,
    direct_reco,
    score,
    structural_bonus,
    tag_overlap,
)

# Un catalogue jouet, mais dont les liens sont ceux du vrai : Death Note et Monster
# sont recommandés l'un à l'autre ; Kimetsu n'a aucun lien avec eux.
WORKS = [
    {
        "title": "Death Note",
        "tags": ["Detective", "Philosophy", "Primarily Male Cast"],
        "genres": ["Mystery", "Thriller"],
        "studios": ["MADHOUSE"],
        "source": "MANGA",
        "year": 2006,
        "relations": {},
        "recommendations": {"Monster": 1151, "Code Geass": 3473, "Psycho-Pass": 200},
    },
    {
        "title": "Monster",
        "tags": ["Detective", "Philosophy", "Primarily Male Cast"],
        "genres": ["Mystery", "Thriller"],
        "studios": ["MADHOUSE"],
        "source": "MANGA",
        "year": 2004,
        "relations": {},
        "recommendations": {"Death Note": 900, "Psycho-Pass": 150},
    },
    {
        "title": "Code Geass",
        "tags": ["Philosophy", "Primarily Male Cast"],
        "genres": ["Mecha"],
        "studios": ["Sunrise"],
        "source": "ORIGINAL",
        "year": 2006,
        "relations": {},
        # Pas de "Psycho-Pass" ici : le fixture original du brief en avait un (90 votes),
        # ce qui créait une arête directe et contredisait le commentaire du test
        # test_co_reco_finds_a_link_with_no_direct_edge ("ne se recommandent pas l'un
        # l'autre"). direct_reco(index, a, b) était alors > 0 alors que le test
        # attendait 0.0 -- bug de fixture, pas de code : direct_reco prend bien "l'arête
        # la plus votée des deux sens" comme documenté, il n'y avait simplement pas
        # censé y avoir d'arête ici.
        "recommendations": {"Death Note": 3000},
    },
    {
        "title": "Psycho-Pass",
        "tags": ["Detective", "Philosophy"],
        "genres": ["Thriller"],
        "studios": ["Production I.G"],
        "source": "ORIGINAL",
        "year": 2012,
        "relations": {},
        "recommendations": {"Death Note": 400, "Monster": 120},
    },
    {
        "title": "Kimetsu no Yaiba",
        "tags": ["Demons", "Swordplay", "Primarily Male Cast"],
        "genres": ["Action"],
        "studios": ["ufotable"],
        "source": "MANGA",
        "year": 2019,
        "relations": {"SEQUEL": ["Mugen Train"]},
        "recommendations": {"Jujutsu Kaisen": 300},
    },
    {
        "title": "Jujutsu Kaisen",
        "tags": ["Demons", "Curses", "Primarily Male Cast"],
        "genres": ["Action"],
        "studios": ["MAPPA"],
        "source": "MANGA",
        "year": 2020,
        "relations": {},
        "recommendations": {"Kimetsu no Yaiba": 250},
    },
    {
        "title": "Mugen Train",
        "tags": ["Demons", "Swordplay"],
        "genres": ["Action"],
        "studios": ["ufotable"],
        "source": "MANGA",
        "year": 2021,
        "relations": {"PREQUEL": ["Kimetsu no Yaiba"]},
        "recommendations": {},
    },
]

INDEX = build_index(WORKS)


def test_the_bug_this_replaces_monster_beats_kimetsu_for_death_note():
    # L'embedding disait l'inverse. C'est LE test de non-régression du design.
    monster = score(INDEX, "Death Note", "Monster").total()
    kimetsu = score(INDEX, "Death Note", "Kimetsu no Yaiba").total()
    assert monster > kimetsu
    # Pas seulement un ordre relatif : sur le vrai catalogue, Death Note ~ Kimetsu
    # est ~ 0.027. Une implémentation dégénérée qui se contenterait de séparer les
    # deux d'un chouïa (par ex. en gardant un bonus de structure fantôme) doit
    # échouer ici même si l'ordre reste correct.
    assert kimetsu < 0.15


def test_a_self_referencing_relation_grants_no_franchise_bonus_to_an_unrelated_work():
    # Le vrai catalogue : 1786/2181 oeuvres (82 %) portent une relation qui se cite
    # elle-même (ex. "DEATH NOTE": {"ADAPTATION": ["DEATH NOTE"]}). Le code d'origine
    # bâtissait un seul ensemble "related" à partir des cibles des relations des DEUX
    # oeuvres, puis testait "b in related or a in related" -- trivialement vrai pour
    # la majorité des oeuvres via leur PROPRE auto-référence, donnant le bonus de
    # franchise maximal (0.15) à des paires sans aucun rapport. Rien dans la fixture
    # existante ne porte d'auto-référence : ce test comble ce trou.
    works = [
        {
            "title": "Death Note",
            "tags": [],
            "genres": [],
            "studios": ["MADHOUSE"],
            "source": "MANGA",
            "year": 2006,
            "relations": {"ADAPTATION": ["Death Note"]},
            "recommendations": {},
        },
        {
            "title": "Nichijou",
            "tags": [],
            "genres": [],
            "studios": ["Kyoto Animation"],
            "source": "MANGA",
            "year": 2011,
            "relations": {},
            "recommendations": {},
        },
    ]
    idx = build_index(works)
    assert structural_bonus(idx, "Death Note", "Nichijou") < BONUS_CAP


def test_the_self_reference_exclusion_is_case_insensitive():
    # Le vrai catalogue compte 55 entrées qui s'auto-référencent sous une casse
    # différente (ex. "VINLAND SAGA" listant ["Vinland Saga"]). La comparaison
    # d'origine était sensible à la casse (`t != a`) : rien ne casse aujourd'hui
    # car aucune paire de titres du catalogue ne diffère uniquement par la casse --
    # mais le correctif ne doit pas reposer sur cette coïncidence. On le prouve en
    # plaçant, à côté de l'auto-référence mal casée, une oeuvre RÉELLEMENT distincte
    # et sans rapport dont le titre est exactement cette variante de casse : sans
    # comparaison insensible à la casse, l'auto-référence est prise pour une vraie
    # relation vers cette autre oeuvre.
    works = [
        {
            "title": "VINLAND SAGA",
            "tags": [],
            "genres": [],
            "studios": ["WIT STUDIO"],
            "source": "MANGA",
            "year": 2019,
            "relations": {"ADAPTATION": ["Vinland Saga"]},
            "recommendations": {},
        },
        {
            "title": "Vinland Saga",
            "tags": [],
            "genres": [],
            "studios": ["MAPPA"],
            "source": "ORIGINAL",
            "year": 2023,
            "relations": {},
            "recommendations": {},
        },
    ]
    idx = build_index(works)
    assert structural_bonus(idx, "VINLAND SAGA", "Vinland Saga") < BONUS_CAP


def test_a_negative_recommendation_contributes_nothing():
    # AniList autorise des votes négatifs (des « non, rien à voir »). Le vrai
    # catalogue en compte 1248. Un vote négatif ne doit ni renforcer le signal, ni
    # -- pire -- rendre la paire plus éloignée qu'une paire sans arête du tout.
    works = [
        {
            "title": "A",
            "tags": [],
            "genres": [],
            "studios": [],
            "source": "MANGA",
            "year": 2000,
            "relations": {},
            "recommendations": {"B": -50},
        },
        {
            "title": "B",
            "tags": [],
            "genres": [],
            "studios": [],
            "source": "MANGA",
            "year": 2000,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "C",
            "tags": [],
            "genres": [],
            "studios": [],
            "source": "MANGA",
            "year": 2000,
            "relations": {},
            "recommendations": {},
        },
    ]
    idx = build_index(works)
    assert direct_reco(idx, "A", "B") == 0.0
    # Pas plus loin qu'une paire sans arête du tout (A, C).
    assert direct_reco(idx, "A", "B") == direct_reco(idx, "A", "C")


def test_a_work_with_no_link_at_all_scores_zero():
    assert score(INDEX, "Death Note", "Kimetsu no Yaiba").direct == 0.0
    assert score(INDEX, "Death Note", "Kimetsu no Yaiba").co_reco == 0.0


def test_direct_reco_is_symmetric_and_takes_the_stronger_edge():
    # Death Note -> Monster (1151) et Monster -> Death Note (900) : on garde 1151.
    assert direct_reco(INDEX, "Death Note", "Monster") == direct_reco(
        INDEX, "Monster", "Death Note"
    )
    assert direct_reco(INDEX, "Death Note", "Monster") > direct_reco(
        INDEX, "Monster", "Psycho-Pass"
    )


def test_co_reco_finds_a_link_with_no_direct_edge():
    # Code Geass et Psycho-Pass ne se recommandent pas l'un l'autre, mais tous deux
    # recommandent Death Note : le public les rapproche. C'est toute la densité du signal.
    assert direct_reco(INDEX, "Code Geass", "Psycho-Pass") == 0.0
    assert co_reco(INDEX, "Code Geass", "Psycho-Pass") > 0.0


def test_a_rare_tag_is_worth_more_than_a_banal_one():
    # "Primarily Male Cast" est porté par presque tout le catalogue ; "Detective" par peu.
    # Deux oeuvres qui ne partagent QUE le tag banal doivent scorer sous deux qui
    # partagent le tag rare.
    banal_only = tag_overlap(
        INDEX, "Code Geass", "Kimetsu no Yaiba"
    )  # Primarily Male Cast
    rare_shared = tag_overlap(
        INDEX, "Death Note", "Psycho-Pass"
    )  # Detective + Philosophy
    assert rare_shared > banal_only


def test_the_structural_bonus_never_carries_a_score_alone():
    # Deux oeuvres du même studio, même source, même décennie -- mais aucun lien de
    # recommandation ni tag partagé -> le bonus est neutralisé.
    lonely = [
        {
            "title": "A",
            "tags": [],
            "genres": [],
            "studios": ["X"],
            "source": "MANGA",
            "year": 2001,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "B",
            "tags": [],
            "genres": [],
            "studios": ["X"],
            "source": "MANGA",
            "year": 2002,
            "relations": {},
            "recommendations": {},
        },
    ]
    idx = build_index(lonely)
    assert structural_bonus(idx, "A", "B") > 0  # le bonus brut existe...
    assert score(idx, "A", "B").total() == 0.0  # ... mais il est porté à zéro


def test_a_franchise_link_is_the_strongest_bonus():
    assert structural_bonus(INDEX, "Kimetsu no Yaiba", "Mugen Train") == pytest.approx(
        BONUS_CAP
    )


def test_the_score_is_bounded():
    assert 0.0 <= score(INDEX, "Death Note", "Monster").total() <= 1.0
    assert score(INDEX, "Death Note", "Death Note").total() <= 1.0


def test_the_weights_are_the_ones_the_spec_measured():
    assert (W_DIRECT, W_CO_RECO, W_TAGS, BONUS_CAP) == (0.45, 0.30, 0.25, 0.15)


def test_a_genre_only_catalogue_produces_a_nonzero_score():
    # La forme "jeu vidéo" du vrai catalogue : tags=0, recommendations=0, mais des
    # genres sur toutes les œuvres. Si le vocabulaire pondéré ignore les genres, ce
    # signal-là est plat et le mode Game entier score zéro partout.
    works = [
        {
            "title": "Game A",
            "tags": [],
            "genres": ["RPG", "Fantasy"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Game B",
            "tags": [],
            "genres": ["RPG", "Fantasy"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Game C",
            "tags": [],
            "genres": ["Shooter"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
    ] + [
        # Remplit le catalogue pour que RPG/Fantasy restent minoritaires : sur 3
        # œuvres seulement, RPG/Fantasy porté par 2/3 tombe à IDF nul (plancher à
        # 0.0, cf. build_index) et ne prouverait rien -- un plancher de fixture, pas
        # un bug du code. Le vrai catalogue jeux (500 œuvres) n'a pas ce problème.
        {
            "title": f"Filler{i}",
            "tags": [],
            "genres": [f"Genre{i}"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        }
        for i in range(8)
    ]
    idx = build_index(works)
    assert tag_overlap(idx, "Game A", "Game B") > 0.0
    assert score(idx, "Game A", "Game B").total() > 0.0


def test_traits_and_organizations_join_the_shared_vocabulary():
    # Forme "personnage" du vrai catalogue (data/processed/filtered_characters.json) :
    # ni tags, ni genres, ni recommandations -- seulement des traits et des
    # organisations (`entities.organizations`). Sans les fondre dans le même
    # vocabulaire pondéré par IDF que tags/genres, ce signal est plat et le mode
    # Personnages ne score jamais rien.
    characters = [
        {
            "name": "Levi",
            "origin": "Shingeki no Kyojin",
            "traits": ["Stoic"],
            "entities": {"organizations": ["Survey Corps"]},
        },
        {
            "name": "Erwin",
            "origin": "Shingeki no Kyojin",
            "traits": ["Charismatic"],
            "entities": {"organizations": ["Survey Corps"]},
        },
        {
            "name": "Random",
            "origin": "Some Other Show",
            "traits": ["Random"],
            "entities": {"organizations": ["Some Other Org"]},
        },
    ] + [
        # Remplit le catalogue pour que "Survey Corps" reste minoritaire (même
        # besoin que RPG/Fantasy dans les fixtures œuvres ci-dessus) : sinon son
        # IDF tombe au plancher 0.0 et ne prouve rien.
        {
            "name": f"Filler{i}",
            "origin": f"Filler Show {i}",
            "traits": [],
            "entities": {"organizations": [f"Org{i}"]},
        }
        for i in range(8)
    ]
    idx = build_index(characters)
    assert tag_overlap(idx, "Levi", "Erwin") > 0.0
    assert tag_overlap(idx, "Levi", "Random") == 0.0


def test_two_characters_from_the_same_work_get_the_franchise_bonus():
    # `origin` est le signal le plus fort qu'un personnage porte : deux
    # personnages de la même œuvre sont structurellement aussi proches qu'une
    # suite directe l'est pour deux œuvres -- ils héritent donc du même bonus
    # plafond, pas d'un petit incrément comme le studio partagé.
    characters = [
        {"name": "Levi", "origin": "Shingeki no Kyojin", "traits": [], "entities": {}},
        {"name": "Erwin", "origin": "Shingeki no Kyojin", "traits": [], "entities": {}},
        {"name": "Naruto", "origin": "Naruto", "traits": [], "entities": {}},
    ]
    idx = build_index(characters)
    assert structural_bonus(idx, "Levi", "Erwin") == pytest.approx(BONUS_CAP)
    assert structural_bonus(idx, "Levi", "Naruto") < BONUS_CAP


def test_a_franchise_tier_bonus_carries_the_score_alone():
    # Deux personnages de la même œuvre qui ne partagent NI trait NI organisation
    # doivent quand même remonter : la même origine EST la preuve de proximité,
    # pas une coïncidence structurelle (studio/source/décennie) que le garde-fou
    # de Components.total() a raison de neutraliser seule. Sans exception pour un
    # bonus au plafond, ce cas retomberait à zéro malgré le lien le plus fort qui
    # existe entre deux personnages -- exactement le trou que l'IMPORTANT 1 pointe.
    characters = [
        {"name": "Levi", "origin": "Shingeki no Kyojin", "traits": [], "entities": {}},
        {"name": "Erwin", "origin": "Shingeki no Kyojin", "traits": [], "entities": {}},
    ]
    idx = build_index(characters)
    components = score(idx, "Levi", "Erwin")
    assert components.direct == 0.0
    assert components.co_reco == 0.0
    assert components.tags == 0.0
    assert components.bonus == pytest.approx(BONUS_CAP)
    assert components.total() > 0.0


def test_a_common_genre_is_worth_much_less_than_a_rare_tag():
    # Le genre n'est qu'un tag très fréquent : la même IDF doit s'appliquer une fois
    # le vocabulaire fusionné. "CommonGenre" est porté par 8 œuvres sur 10 (banal) ;
    # "Detective"/"Philosophy" par 2 seulement (rare). Partager le genre banal doit
    # valoir beaucoup moins que partager les tags rares.
    works = [
        {
            "title": "Code Geass2",
            "tags": ["Philosophy"],
            "genres": ["Mecha", "CommonGenre"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Kimetsu2",
            "tags": ["Demons", "Swordplay"],
            "genres": ["Action", "CommonGenre"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Death Note2",
            "tags": ["Detective", "Philosophy"],
            "genres": ["Mystery"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Psycho-Pass2",
            "tags": ["Detective", "Philosophy"],
            "genres": ["SciFi"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
    ] + [
        {
            "title": f"Filler{i}",
            "tags": [],
            "genres": ["CommonGenre", f"Filler{i}Genre"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        }
        for i in range(6)
    ]
    idx = build_index(works)
    banal_only = tag_overlap(
        idx, "Code Geass2", "Kimetsu2"
    )  # ne partagent que CommonGenre
    rare_shared = tag_overlap(
        idx, "Death Note2", "Psycho-Pass2"
    )  # Detective + Philosophy
    # Le genre partagé doit compter (> 0 : preuve qu'il entre bien dans le vocabulaire
    # fusionné), mais peser beaucoup moins que les tags rares partagés.
    assert banal_only > 0.0
    assert rare_shared > banal_only
    assert banal_only < 0.1
    assert rare_shared > 0.5
