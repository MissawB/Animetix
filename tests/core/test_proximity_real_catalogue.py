"""La batterie de paires de référence, sur le VRAI catalogue.

La spec appelle ces paires « le test qui aurait attrapé le bug d'aujourd'hui ».
Épinglées contre un fixture jouet de 7 œuvres -- dont les arêtes de recommandation
ont été écrites pour produire la réponse attendue -- elles ne peuvent rien attraper :
ni une régression de données, ni un changement de schéma d'ingestion, ni un
réglage de poids. Ici, on charge data/processed/clean_root_animes.json et on
mesure sur les 2 181 œuvres réelles.

Le fichier est suivi par Git LFS : la CI récupère les POINTEURS sans les objets
(un fichier texte de ~130 octets sur lequel json.load meurt). On saute proprement
dans ce cas -- un skip est honnête, un faux vert ne l'est pas.
"""

import json
from pathlib import Path

import pytest
from core.domain.services.proximity.components import build_index, score
from core.domain.services.proximity.service import HOT_FLOOR, ProximityService

CATALOGUE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "clean_root_animes.json"
)

# Titres tels qu'ils apparaissent dans le catalogue (casse exacte).
DEATH_NOTE = "DEATH NOTE"
MONSTER = "MONSTER"
KIMETSU = "Kimetsu no Yaiba"


def _load_real_works():
    if not CATALOGUE.exists():
        pytest.skip(f"Catalogue réel absent : {CATALOGUE}")
    raw = CATALOGUE.read_bytes()
    if raw[:7] == b"version" or len(raw) < 1000:
        # Un pointeur Git LFS non résolu ("version https://git-lfs..."), pas des données.
        pytest.skip(
            "Catalogue réel = pointeur Git LFS non récupéré (objets LFS absents)"
        )
    works = json.loads(raw.decode("utf-8"))
    titles = {w.get("title") for w in works}
    if not {DEATH_NOTE, MONSTER, KIMETSU} <= titles:
        pytest.skip("Catalogue réel présent mais sans les paires de référence")
    return works


@pytest.fixture(scope="module")
def real_index():
    return build_index(_load_real_works())


@pytest.fixture(scope="module")
def real_service():
    works = _load_real_works()
    from unittest.mock import MagicMock

    catalog = MagicMock()
    catalog.load_data.return_value = {"db": works}
    return ProximityService(catalog_service=catalog)


def test_the_reference_pair_holds_on_the_real_catalogue(real_index):
    # LE test de non-régression du design, enfin sur les vraies données :
    # l'embedding classait Kimetsu (0,671) plus proche de Death Note que Monster
    # (0,654), sur un plancher de bruit à 0,583. Mesuré ici : 0,686 vs 0,035.
    monster = score(real_index, DEATH_NOTE, MONSTER).total()
    kimetsu = score(real_index, DEATH_NOTE, KIMETSU).total()
    assert monster > kimetsu
    assert monster > 0.5  # un vrai voisin, pas une victoire d'un cheveu
    assert kimetsu < 0.15  # et une œuvre sans rapport reste sans rapport


def test_monster_is_the_closest_work_to_death_note_in_the_whole_catalogue(real_index):
    best = max(
        (
            (score(real_index, DEATH_NOTE, title).total(), title)
            for title in real_index.works
            if title != DEATH_NOTE
        ),
    )
    assert best[1] == MONSTER


def test_the_hot_floor_keeps_the_contents_to_a_handful_of_the_real_catalogue(
    real_index,
):
    # IMPORTANT 2, mesuré : avec le seul percentile, 436 œuvres (20 % du catalogue)
    # franchissaient HOT face à DEATH NOTE et se voyaient offrir trois de ses tags.
    # Le plancher de score brut est ce qui rend « à 80 %, le joueur est déjà très
    # proche » vrai sur des données à longue traîne.
    totals = [
        score(real_index, DEATH_NOTE, title).total()
        for title in real_index.works
        if title != DEATH_NOTE
    ]
    hot = [t for t in totals if t >= HOT_FLOOR]
    assert len(hot) < 0.03 * len(totals)  # < 3 % du catalogue, pas 20 %


def test_a_banal_neighbour_of_death_note_learns_nothing_on_the_real_catalogue(
    real_service,
):
    # Kimetsu no Yaiba : 0,035 de score brut. Quel que soit son percentile (57,6 %
    # -- la traîne du catalogue est longue), elle ne doit RIEN apprendre au joueur.
    report = real_service.report("Anime", DEATH_NOTE, KIMETSU)
    assert report["reasons"] == []


def test_the_real_neighbour_of_death_note_is_told_what_earned_it(real_service):
    report = real_service.report("Anime", DEATH_NOTE, MONSTER)
    assert report["percent"] == 100.0  # rien n'est plus proche
    assert report["reasons"]
    assert any(r["detail"] for r in report["reasons"])
