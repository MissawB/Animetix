"""Behavior coverage tests for VsBattleService.

Complements test_vs_battle_service.py. Exercises the real parsing/matching logic:
JSON extraction (clean, fenced, embedded, nested), name/franchise matching,
structured-generation fallback, image recovery + SSRF gating, synthetic profile
generation when the wiki page is missing, tier extraction, and verse handling.

All inference/LLM, fandom catalog, prompt manager and web search are mocked;
assertions check the REAL parsed structures and decisions.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from core.domain.entities.ai_schemas import CombatCharacter
from core.domain.services.creative.vs_battle_service import VsBattleService
from core.domain.services.prompt_manager import PromptManager
from core.ports.fandom_port import FandomPort
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort


@pytest.fixture
def fandom():
    return MagicMock(spec=FandomPort)


@pytest.fixture
def inference():
    return MagicMock(spec=InferencePort)


@pytest.fixture
def prompts():
    pm = MagicMock(spec=PromptManager)
    pm.get_prompt.return_value = ("prompt", "system")
    return pm


@pytest.fixture
def web():
    return MagicMock(spec=WebSearchPort)


@pytest.fixture
def service(fandom, inference, prompts, web):
    return VsBattleService(
        fandom_port=fandom,
        inference_engine=inference,
        prompt_manager=prompts,
        web_search_port=web,
    )


# --- _normalize_anime_name ----------------------------------------------


def test_normalize_strips_parens_and_vowels(service):
    assert service._normalize_anime_name("Naruto (Shippuden)") == "naruto"
    assert service._normalize_anime_name("Yuuki") == "yuki"


# --- _is_franchise_match -------------------------------------------------


def test_is_franchise_match_empty_franchise_is_true(service):
    assert service._is_franchise_match("", [], "Anything") is True


def test_is_franchise_match_in_title(service):
    assert service._is_franchise_match("Naruto", [], "Naruto Uzumaki") is True


def test_is_franchise_match_in_categories(service):
    assert (
        service._is_franchise_match("Bleach", ["Bleach Characters"], "Ichigo") is True
    )


def test_is_franchise_match_no_match(service):
    assert service._is_franchise_match("OnePiece", ["Bleach"], "Ichigo") is False


# --- _is_name_match ------------------------------------------------------


def test_is_name_match_full_overlap(service):
    assert service._is_name_match("Naruto Uzumaki", "Naruto Uzumaki") is True


def test_is_name_match_last_name_conflict_rejected(service):
    # Same first token, very different last name -> rejected by SequenceMatcher gate.
    assert service._is_name_match("Naruto Uzumaki", "Naruto Smithington") is False


def test_is_name_match_franchise_matched_first_token(service):
    assert (
        service._is_name_match(
            "Goku Black", "Goku (Dragon Ball)", franchise_matched=True
        )
        is True
    )


def test_is_name_match_loose_partial(service):
    assert service._is_name_match("Monkey D Luffy", "Luffy", loose=True) is True


def test_is_name_match_single_token_substring(service):
    # No multi-letter parts on one side -> substring containment path.
    assert service._is_name_match("A", "A B C") is True


# --- _extract_json -------------------------------------------------------


def test_extract_json_from_clean_string(service):
    data = service._extract_json('{"name": "X", "stats": {"tier": "5-B"}}')
    assert data["name"] == "X"


def test_extract_json_from_dict_passthrough(service):
    obj = {"name": "X", "tier": "5-B"}
    assert service._extract_json(obj) == obj


def test_extract_json_from_fenced_block(service):
    text = 'Here it is:\n```json\n{"name": "Z", "winner": "Z"}\n```\nDone'
    assert service._extract_json(text)["name"] == "Z"


def test_extract_json_from_embedded_braces(service):
    text = 'noise {"name": "E", "summary": "hi"} trailing noise'
    assert service._extract_json(text)["name"] == "E"


def test_extract_json_strips_after_separator(service):
    text = '{"name": "S", "tier": "1-A"}\n---\nignored trailing garbage {bad'
    assert service._extract_json(text)["name"] == "S"


def test_extract_json_raises_when_no_json(service):
    with pytest.raises(ValueError, match="Could not extract valid JSON"):
        service._extract_json("absolutely no json here")


def test_find_best_dict_picks_nested_match(service):
    obj = {"wrapper": {"data": {"name": "Deep", "tier": "2-A", "speed": "fast"}}}
    best = service._find_best_dict(obj)
    assert best["name"] == "Deep"


def test_find_best_dict_searches_lists(service):
    obj = [{"irrelevant": 1}, {"name": "L", "winner": "L"}]
    assert service._find_best_dict(obj)["name"] == "L"


# --- _safe_generate_structured ------------------------------------------


def test_safe_generate_structured_primary_success(service, inference):
    inference.generate.return_value = json.dumps(
        {"name": "Hero", "stats": {"tier": "5-B"}}
    )
    char = service._safe_generate_structured("p", "s", CombatCharacter)
    assert char.name == "Hero"
    inference.generate.assert_called_once()


def test_safe_generate_structured_falls_back_on_primary_failure(service, inference):
    # First call (json_mode) raises; fallback call returns valid JSON.
    inference.generate.side_effect = [
        RuntimeError("json mode unsupported"),
        json.dumps({"name": "Fallback", "stats": {"tier": "3-A"}}),
    ]
    char = service._safe_generate_structured("p", "s", CombatCharacter)
    assert char.name == "Fallback"
    assert inference.generate.call_count == 2


# --- _recover_image (SSRF gating) ---------------------------------------


def test_recover_image_returns_none_without_web_port(fandom, inference, prompts):
    svc = VsBattleService(fandom, inference, prompts, web_search_port=None)
    assert svc._recover_image("Goku", "DBZ") is None


def test_recover_image_returns_safe_image_url(service, web):
    web.search.return_value = [
        {"url": "https://media.example.com/goku.jpg"},
        {"url": "https://media.example.com/other.png"},
    ]
    with patch(
        "core.domain.services.creative.vs_battle_service.is_safe_url",
        return_value=True,
    ):
        url = service._recover_image("Goku", "DBZ")
    assert url == "https://media.example.com/goku.jpg"


def test_recover_image_skips_unsafe_url(service, web):
    web.search.return_value = [{"url": "https://internal.example/private.jpg"}]
    with patch(
        "core.domain.services.creative.vs_battle_service.is_safe_url",
        return_value=False,
    ):
        assert service._recover_image("Goku", "DBZ") is None


def test_recover_image_handles_search_exception(service, web):
    web.search.side_effect = RuntimeError("search down")
    assert service._recover_image("Goku", "DBZ") is None


# --- _map_tier_to_value / _extract_max_tier -----------------------------


def test_extract_max_tier_picks_highest(service):
    # "7-C" -> 32, "1-A" -> 95: best should be the 1-A fragment.
    assert service._extract_max_tier("7-C | 1-A").strip() == "1-A"


def test_extract_max_tier_single(service):
    assert service._extract_max_tier("5-B").strip() == "5-B"


# --- fetch_character_versions: synthetic generation ---------------------


def test_fetch_versions_generates_synthetic_when_no_wiki(
    service, fandom, inference, web
):
    # Catalog returns nothing in both strict and loose passes.
    fandom.fetch_character_data.return_value = []
    inference.generate.return_value = json.dumps(
        {"name": "Original", "stats": {"tier": "4-A"}}
    )
    web.search.return_value = []  # image recovery yields nothing

    versions = service.fetch_character_versions("Madeup Hero", franchise="Nowhere")

    assert len(versions) == 1
    char = versions[0]
    assert char.name == "Madeup Hero (AI Generated)"
    assert char.franchise == "Nowhere"
    assert "vsbattles.fandom.com/wiki/Madeup_Hero" in char.wiki_url
    # 4-A maps to 55.
    assert char.stats.tier_value == 55


def test_fetch_versions_synthetic_failure_returns_empty(service, fandom, inference):
    fandom.fetch_character_data.return_value = []
    inference.generate.side_effect = RuntimeError("LLM totally down")
    assert service.fetch_character_versions("Ghost", franchise="X") == []


# --- fetch_character_versions: wiki parse path --------------------------


def test_fetch_versions_parses_wiki_candidate(service, fandom, inference):
    fandom.fetch_character_data.return_value = [
        {
            "name": "Ichigo Kurosaki",
            "url": "https://vsbattles.fandom.com/wiki/Ichigo",
            "image_url": "https://img.example/ichigo.png",
            "categories": ["Bleach Characters"],
            "wikitext": "Intro text...\n'''Tier:''' 5-A, possibly higher\nmore",
        }
    ]
    inference.generate.return_value = json.dumps(
        {"name": "parsed", "stats": {"tier": "5-A"}}
    )

    with patch("time.sleep"):
        versions = service.fetch_character_versions("Ichigo", franchise="Bleach")

    assert len(versions) == 1
    c = versions[0]
    assert c.name == "Ichigo Kurosaki"  # overwritten from raw_data
    assert c.wiki_url == "https://vsbattles.fandom.com/wiki/Ichigo"
    assert c.image_url == "https://img.example/ichigo.png"
    assert c.stats.tier_value == 48  # 5-A


def test_fetch_versions_skips_unparseable_candidate(service, fandom, inference):
    fandom.fetch_character_data.return_value = [
        {
            "name": "Ichigo Kurosaki",
            "categories": ["Bleach"],
            "wikitext": "'''Speed:''' fast stuff here",
        }
    ]
    inference.generate.side_effect = RuntimeError("parse exploded")
    with patch("time.sleep"):
        versions = service.fetch_character_versions("Ichigo", franchise="Bleach")
    assert versions == []  # parse failure swallowed, no version added


def test_fetch_versions_verse_estimate_when_loose(service, fandom, inference, web):
    # Strict pass: nothing matches the name. Loose pass: a "Verse" page appears.
    def candidates(query):
        if "Verse" in query:
            return [{"name": "Bleach Verse", "categories": [], "wikitext": "x"}]
        return []

    fandom.fetch_character_data.side_effect = candidates
    inference.generate.return_value = json.dumps(
        {"name": "verse", "stats": {"tier": "3-A"}}
    )
    web.search.return_value = []
    with patch("time.sleep"):
        versions = service.fetch_character_versions("Nobody", franchise="Bleach")
    assert len(versions) == 1
    assert versions[0].name == "Nobody (Verse Estimate)"


# --- fetch_and_parse_character: best-of selection -----------------------


def test_fetch_and_parse_picks_highest_tier(service):
    low = CombatCharacter.model_validate({"name": "Low", "stats": {"tier": "9-C"}})
    high = CombatCharacter.model_validate({"name": "High", "stats": {"tier": "1-A"}})
    low.stats.tier_value = service._map_tier_to_value("9-C")
    high.stats.tier_value = service._map_tier_to_value("1-A")
    with patch.object(service, "fetch_character_versions", return_value=[low, high]):
        best = service.fetch_and_parse_character("X")
    assert best.name == "High"


def test_fetch_and_parse_raises_when_no_versions(service):
    with patch.object(service, "fetch_character_versions", return_value=[]):
        with pytest.raises(ValueError, match="Could not successfully parse"):
            service.fetch_and_parse_character("Nobody")
