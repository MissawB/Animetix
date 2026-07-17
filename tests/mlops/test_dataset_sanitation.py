# -*- coding: utf-8 -*-
"""Garde-fous : le dataset généré est ancré, sans slot numérique, sans squelette."""

import collections
import json
import os
import re
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)  # racine repo -> permet `import tests.mlops...`
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))  # -> permet `import pipeline...`

import pipeline.mlops.finetuning_dataset as fd  # noqa: E402

from tests.mlops.test_finetuning_dataset import _orchestrator_env  # noqa: E402

BANNED_PHRASES = [
    "jouit d'une immense popularité",
    "figure incontournable",
    "se plaçant au rang numéro",
    "incarne les valeurs et les conflits majeurs",
    "votes d'admiration",
    "avec pas moins de",
    "ranking at number",
    "votes of admiration",
    "no less than",
]
BANNED_NUMERIC = [
    re.compile(r"rang num[ée]ro\s+\d+", re.IGNORECASE),
    re.compile(r"\d+\s+votes", re.IGNORECASE),
    re.compile(r"number\s+\d+\s+of favorite", re.IGNORECASE),
    re.compile(r"\d[\d,]*\s+(members|membres)", re.I),
]

# Le routage langue est positionnel : idx pair -> FR (structuré, PAS de synopsis),
# idx impair -> EN (synopsis réel intégré). Les entités dont on veut vérifier
# l'ANCRAGE (demon lord / swordsman) DOIVENT donc être à un index IMPAIR.
ANIMES = [
    # idx 0 -> FR (structuré, pas de synopsis) : remplisseur
    {
        "title": "BetaWork",
        "genres": ["Comedy"],
        "studios": ["StudioY"],
        "tags": ["school"],
        "popularity": 1000,
        "year": 2015,
        "description": "BetaHero navigates a chaotic high-school life full of clubs.",
    },
    # idx 1 -> EN (synopsis ancré) : AlphaWork, Tier-1
    {
        "title": "AlphaWork",
        "genres": ["Action"],
        "studios": ["StudioX"],
        "tags": ["ninja"],
        "popularity": 200000,
        "year": 2002,
        "description": "AlphaHero trains hard to protect his village from the demon lord.",
    },
]
MANGAS = [
    {
        "title": "FillerManga",
        "genres": ["Action"],
        "tags": ["t"],
        "popularity": 1000,
        "year": 2005,
        "description": "A filler manga synopsis.",
    },
]
CHARS = [
    # idx 0 -> FR (structuré) : remplisseur
    {
        "name": "DeltaChar",
        "origin": "DeltaWork",
        "entities": {"organizations": []},
        "popularity": {"favourites": 100, "rank": 9},
        "metadata": {},
        "biography": "A filler biography.",
    },
    # idx 1 -> EN (biographie ancrée) : GammaHero, Tier-1
    {
        "name": "GammaHero",
        "origin": "GammaOrigin",
        "entities": {"organizations": ["Survey Corps"]},
        "popularity": {"favourites": 3000, "rank": 7},
        "metadata": {"height": "180 cm"},
        "biography": "GammaHero is a fearless swordsman who lost his family to demons.",
    },
]


def _generate(tmp):
    with _orchestrator_env(
        tmp,
        animes=ANIMES,
        mangas=[],
        chars=CHARS,
        env={"ANIMETIX_AUGMENT_DATA": "False", "ANIMETIX_QUERY_NOISE_RATE": "0.0"},
    ) as out:
        fd.run_generate_instruction_dataset()
        with open(out, encoding="utf-8") as f:
            return [json.loads(line) for line in f]


def _specialized_outputs(data):
    """Sorties dont l'instruction cite une de nos entités-fixtures (donc générées ici)."""
    entities = ("AlphaWork", "BetaWork", "GammaHero")
    outs = []
    for it in data:
        if "turns" in it:
            continue
        text = it.get("instruction", "") + " " + it.get("output", "")
        if any(e in text for e in entities):
            outs.append(it["output"])
    return outs


# Garde-fou anti-collision : Zeta doit tomber sur la branche ANGLAISE (idx impair),
# car seule l'amorce EN[0] ("{name} is a character from '{origin}'.") est byte-identique
# à l'aux1 EN. Un remplisseur (favs>50 pour rester dans top_chars) occupe idx 0 -> FR,
# poussant Zeta à idx 1 -> EN. Zeta est SANS biographie NI organisation : sa sortie
# primaire dégénère en amorce seule, donc collision avec aux1 quand EN[0] est tiré.
CHARS_COLLISION = [
    {
        "name": "FillerColl",
        "origin": "FillerWork",
        "entities": {"organizations": []},
        "popularity": {"favourites": 100, "rank": 9},
        "metadata": {},
        "biography": "A filler biography.",
    },
    {
        "name": "Zeta",
        "origin": "OmegaWork",
        "entities": {"organizations": []},
        "popularity": {"favourites": 1500, "rank": 3},
        "metadata": {},
        "biography": "",
    },
]


class TestDatasetSanitation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = _generate(self._tmp.name)
        self.outs = _specialized_outputs(self.data)
        self.assertTrue(self.outs, "aucune sortie spécialisée générée")

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_banned_phrases(self):
        for o in self.outs:
            for phrase in BANNED_PHRASES:
                self.assertNotIn(phrase, o, f"phrase bannie: {phrase!r}")

    def test_no_unconditioned_numeric_noise(self):
        for o in self.outs:
            for rx in BANNED_NUMERIC:
                self.assertIsNone(
                    rx.search(o), f"bruit numérique: {rx.pattern} dans {o!r}"
                )

    def test_outputs_are_grounded(self):
        joined = " ".join(self.outs)
        # faits réels tirés des descriptions/biographie
        self.assertIn("demon lord", joined)
        self.assertIn("swordsman", joined)

    def test_no_duplicate_outputs_per_entity(self):
        alpha = [
            it["output"] for it in self.data if "AlphaWork" in it.get("instruction", "")
        ]
        self.assertEqual(
            len(alpha), len(set(alpha)), "sorties dupliquées pour AlphaWork"
        )

    def test_form_diversity_no_dominant_8gram(self):
        grams = collections.Counter()
        for o in self.outs:
            toks = o.split()
            for i in range(len(toks) - 7):
                grams[" ".join(toks[i : i + 8])] += 1
        if grams:
            top = grams.most_common(1)[0][1]
            self.assertLessEqual(
                top / len(self.outs),
                0.5,
                "un 8-gramme domine les sorties (squelette ?)",
            )

    def test_no_banned_phrases_in_dialogue_turns(self):
        # IMPORTANT : l'orchestrateur MOCKE generate_multiturn_dialogues, donc on
        # appelle la VRAIE fonction directement pour tester les dialogues réels.
        from pipeline.mlops.finetuning_dataset import generate_multiturn_dialogues

        vocab = {
            "Tsundere": {
                "definition": "d",
                "examples": "e",
                "impact": "i",
                "origin": "o",
            }
        }
        dialogues = generate_multiturn_dialogues(ANIMES, MANGAS, CHARS, vocab, count=14)
        for d in dialogues:
            for t in d["turns"]:
                for phrase in BANNED_PHRASES:
                    self.assertNotIn(
                        phrase, t["assistant"], f"phrase bannie (dialogue): {phrase!r}"
                    )

    def test_no_numeric_noise_in_dialogue_turns(self):
        from pipeline.mlops.finetuning_dataset import generate_multiturn_dialogues

        vocab = {
            "Tsundere": {
                "definition": "d",
                "examples": "e",
                "impact": "i",
                "origin": "o",
            }
        }
        dialogues = generate_multiturn_dialogues(ANIMES, MANGAS, CHARS, vocab, count=14)
        for d in dialogues:
            for t in d["turns"]:
                for rx in BANNED_NUMERIC:
                    self.assertIsNone(
                        rx.search(t["assistant"]),
                        f"bruit numérique (dialogue): {rx.pattern}",
                    )

    def test_collision_guard_keeps_outputs_distinct(self):
        # Zeta (branche EN, sans bio ni org) : sur plusieurs graines, le garde-fou
        # doit (a) empêcher toute sortie dupliquée, et (b) être RÉELLEMENT exercé —
        # sinon le test serait vacui (passerait même si le garde-fou était retiré).
        # Le garde-fou "a agi" quand aux1 == primary est supprimé -> il ne reste
        # que la sortie primaire pour Zeta (len == 1).
        # NB : profile_builders.py utilise random.SystemRandom() pour l'amorce, donc
        # celle-ci n'est PAS pilotée par le seed -> 60 graines pour fiabiliser le test.
        guard_fired = False
        for seed in range(60):
            with tempfile.TemporaryDirectory() as tmp:
                with _orchestrator_env(
                    tmp,
                    animes=[],
                    mangas=[],
                    chars=CHARS_COLLISION,
                    seed=seed,
                    env={
                        "ANIMETIX_AUGMENT_DATA": "False",
                        "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                    },
                ) as out:
                    fd.run_generate_instruction_dataset()
                    with open(out, encoding="utf-8") as f:
                        data = [json.loads(line) for line in f]
            zeta = [
                it["output"]
                for it in data
                if "turns" not in it and "Zeta" in it.get("instruction", "")
            ]
            self.assertTrue(zeta, f"aucune sortie Zeta (seed={seed})")
            self.assertEqual(
                len(zeta),
                len(set(zeta)),
                f"sortie dupliquée pour Zeta (seed={seed}) : garde-fou HS",
            )
            if len(zeta) == 1:  # aux1 supprimé car byte-identique à primary
                guard_fired = True
        self.assertTrue(
            guard_fired,
            "le garde-fou anti-collision n'a jamais été exercé sur 60 graines : "
            "le fixture ne provoque pas la collision -> test vacui",
        )


if __name__ == "__main__":
    unittest.main()
