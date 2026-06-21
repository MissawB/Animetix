"""Behavior tests for the expert-facts enrichment pipeline.

`run_expert_enrichment()` computes file paths from ``__file__`` and does real
``open`` / ``os.path.exists`` / ``json`` / ``yaml`` calls. We patch those names
*inside the module namespace* so no real filesystem I/O happens, then assert on
the actual transformed data captured from ``json.dump``.
"""

from unittest.mock import mock_open

import pipeline.expert_enrichment as ee

# A fact whose prefix (first 30 chars) is distinctive and > 30 chars long.
NARUTO_FACT = (
    "Naruto Uzumaki est le septieme Hokage du village de Konoha et le "
    "hote de Kurama, le demon-renard a neuf queues."
)
ONEPIECE_FACT = (
    "One Piece raconte l'aventure de Monkey D. Luffy, un pirate au corps "
    "elastique en quete du tresor legendaire."
)

FACTS = {
    "expert_facts": [
        {"primary_keywords": ["Naruto"], "fact": NARUTO_FACT},
        {"primary_keywords": ["One Piece"], "fact": ONEPIECE_FACT},
    ]
}


def _wire(mocker, facts, files):
    """Patch the module namespace.

    ``files`` maps a *substring* of a path to its parsed JSON item-list. A path
    is reported as "existing" only if it is FACTS_FILE or appears in ``files``.
    The captured ``json.dump`` mock is returned so tests can read what was
    written back.
    """
    facts_present = facts is not None

    def exists(path):
        if path.endswith("expert_facts.yaml"):
            return facts_present
        return any(key in path for key in files)

    mocker.patch.object(ee.os.path, "exists", side_effect=exists)
    mocker.patch.object(ee, "open", mock_open(), create=True)
    mocker.patch.object(ee.yaml, "safe_load", return_value=facts)

    # json.load is called once per *existing* data file, in declaration order
    # (Anime, Manga, Character). Build the ordered side-effect list.
    ordered_payloads = []
    for key in _ordered_existing(files):
        ordered_payloads.append(files[key])
    mocker.patch.object(ee.json, "load", side_effect=ordered_payloads)

    dump = mocker.patch.object(ee.json, "dump")
    return dump


# The module processes ANIME_FILE, MANGA_FILE, CHAR_FILE in this order.
_FILE_ORDER = ["clean_root_animes", "clean_root_mangas", "filtered_characters"]


def _ordered_existing(files):
    return [k for k in _FILE_ORDER if k in files]


def _dumped(dump_mock):
    """Return the list of data objects passed to each json.dump call, in order."""
    return [call.args[0] for call in dump_mock.call_args_list]


# --- 1. Missing facts file ----------------------------------------------


def test_missing_facts_file_returns_early(mocker):
    err = mocker.patch.object(ee.logger, "error")
    dump = _wire(mocker, facts=None, files={"clean_root_animes": [{"title": "Naruto"}]})

    ee.run_expert_enrichment()

    err.assert_called_once()
    dump.assert_not_called()  # nothing written when facts file is absent


# --- 2. Keyword match prepends fact + creates synopsis_fr ----------------


def test_match_prepends_fact_and_creates_synopsis(mocker):
    item = {"title": "Naruto", "description": "Un ninja."}
    dump = _wire(mocker, FACTS, {"clean_root_animes": [item]})

    ee.run_expert_enrichment()

    written = _dumped(dump)[0][0]
    assert written["description"] == f"{NARUTO_FACT}\n\nUn ninja."
    # synopsis_fr is created from the (now original) description, then the fact
    # is prepended to it too.
    assert written["synopsis_fr"].startswith(NARUTO_FACT)
    assert "Un ninja." in written["synopsis_fr"]


# --- 3. Idempotence ------------------------------------------------------


def test_idempotent_when_prefix_already_present(mocker):
    # Description already begins with the fact -> must not be prepended again.
    pre_desc = f"{NARUTO_FACT}\n\nUn ninja."
    item = {
        "title": "Naruto",
        "description": pre_desc,
        "synopsis_fr": pre_desc,
    }
    dump = _wire(mocker, FACTS, {"clean_root_animes": [item]})

    ee.run_expert_enrichment()

    written = _dumped(dump)[0][0]
    assert written["description"] == pre_desc  # unchanged, no double prepend
    assert written["description"].count(NARUTO_FACT[:30]) == 1
    assert written["synopsis_fr"] == pre_desc
    assert written["synopsis_fr"].count(NARUTO_FACT[:30]) == 1


# --- 4. Field selection --------------------------------------------------


def test_uses_clean_description_field(mocker):
    item = {"name": "Naruto", "clean_description": "Bio nettoyee."}
    dump = _wire(mocker, FACTS, {"filtered_characters": [item]})

    ee.run_expert_enrichment()

    written = _dumped(dump)[0][0]
    assert written["clean_description"] == f"{NARUTO_FACT}\n\nBio nettoyee."
    assert "description" not in written  # the plain field was never introduced


def test_uses_biography_field_when_no_description(mocker):
    item = {"name": "Naruto", "biography": "Histoire du personnage."}
    dump = _wire(mocker, FACTS, {"filtered_characters": [item]})

    ee.run_expert_enrichment()

    written = _dumped(dump)[0][0]
    assert written["biography"] == f"{NARUTO_FACT}\n\nHistoire du personnage."
    assert "clean_description" not in written


# --- 5. No match leaves item untouched -----------------------------------


def test_no_keyword_match_leaves_item_unchanged(mocker):
    item = {"title": "Bleach", "description": "Un shinigami."}
    dump = _wire(mocker, FACTS, {"clean_root_animes": [item]})

    ee.run_expert_enrichment()

    written = _dumped(dump)[0][0]
    assert written == {"title": "Bleach", "description": "Un shinigami."}
    assert "synopsis_fr" not in written  # no synopsis created without a match


# --- 6. Missing data file is skipped, others still process ---------------


def test_missing_data_file_skipped_others_processed(mocker):
    warn = mocker.patch.object(ee.logger, "warning")
    # Anime + Character exist; Manga file is absent.
    anime_item = {"title": "Naruto", "description": "Ninja."}
    char_item = {"name": "One Piece world", "clean_description": "Monde."}
    dump = _wire(
        mocker,
        FACTS,
        {
            "clean_root_animes": [anime_item],
            "filtered_characters": [char_item],
        },
    )

    ee.run_expert_enrichment()

    # Exactly two files were written (manga skipped), and a warning was logged.
    assert dump.call_count == 2
    warn.assert_called_once()
    assert "clean_root_mangas" in warn.call_args.args[0]

    anime_written = _dumped(dump)[0][0]
    char_written = _dumped(dump)[1][0]
    assert anime_written["description"].startswith(NARUTO_FACT)
    assert char_written["clean_description"].startswith(ONEPIECE_FACT)
