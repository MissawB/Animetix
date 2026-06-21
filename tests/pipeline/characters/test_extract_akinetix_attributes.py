"""Behavior tests for the Akinetix binary-attribute extraction pipeline.

Covers:
- ``extract_binary_attributes``: no-BRAIN early return, the real prompt/payload
  sent to the Brain API, JSON extraction from a noisy LLM reply, the
  no-JSON-found and non-200 branches, and exception resilience.
- ``simulate_binary_attributes``: keyword -> attribute rule mapping.
- ``run_extraction``: missing input, all-already-done short-circuit, the real
  transform + idempotent OUTPUT_FILE write, the incremental skip of already
  enriched ids, and the LLM-then-simulation fallback.

All HTTP and file paths are mocked in the module namespace; real file content is
fed via ``tmp_path``. No real network, DB, or model work happens.
"""

import json
from unittest.mock import MagicMock

import pipeline.characters.extract_akinetix_attributes as ak


def _resp(status, payload=None, text=""):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload or {}
    r.text = text
    return r


# --- extract_binary_attributes ------------------------------------------


def test_extract_returns_none_without_brain_url(mocker):
    mocker.patch.object(ak, "BRAIN_URL", None)
    assert ak.extract_binary_attributes("Guts", "swordsman", {}) is None


def test_extract_parses_json_from_noisy_reply(mocker):
    mocker.patch.object(ak, "BRAIN_URL", "http://brain")
    reply = 'Sure!\n{"attributes": {"porte_une_epee": true, "a_des_cheveux_blonds": false}}\nDone'
    http = mocker.patch.object(
        ak, "safe_http_request", return_value=_resp(200, {"text": reply})
    )
    result = ak.extract_binary_attributes("Guts", "wields a sword", {})
    assert result == {"porte_une_epee": True, "a_des_cheveux_blonds": False}

    # Real request shape: POST to /generate with prompt + system_prompt + key.
    args, kwargs = http.call_args
    assert args[0] == "POST"
    assert args[1].endswith("/generate")
    assert "Guts" in kwargs["json"]["prompt"]
    assert "system_prompt" in kwargs["json"]
    assert kwargs["headers"]["X-API-Key"] == ak.BRAIN_API_KEY
    assert kwargs["allow_internal"] is True


def test_extract_returns_none_when_no_json(mocker):
    mocker.patch.object(ak, "BRAIN_URL", "http://brain")
    mocker.patch.object(
        ak, "safe_http_request", return_value=_resp(200, {"text": "no json here"})
    )
    assert ak.extract_binary_attributes("Guts", "x", {}) is None


def test_extract_returns_none_on_non_200(mocker):
    mocker.patch.object(ak, "BRAIN_URL", "http://brain")
    mocker.patch.object(
        ak, "safe_http_request", return_value=_resp(500, text="server error")
    )
    assert ak.extract_binary_attributes("Guts", "x", {}) is None


def test_extract_returns_none_on_exception(mocker):
    mocker.patch.object(ak, "BRAIN_URL", "http://brain")
    mocker.patch.object(ak, "safe_http_request", side_effect=RuntimeError("boom"))
    assert ak.extract_binary_attributes("Guts", "x", {}) is None


# --- simulate_binary_attributes -----------------------------------------


def test_simulate_maps_keywords_to_attributes():
    attrs = ak.simulate_binary_attributes(
        "Hero", "He wields a sword and uses magic with super power at school"
    )
    assert attrs == {
        "porte_une_epee": True,
        "utilise_la_magie": True,
        "est_un_lyceen": True,
        "possede_des_super_pouvoirs": True,
    }


def test_simulate_french_keywords_and_blonde_hair():
    attrs = ak.simulate_binary_attributes(
        "Heros", "il porte une épée, des cheveux blonds, de la magie au lycée"
    )
    assert attrs == {
        "porte_une_epee": True,
        "a_des_cheveux_blonds": True,
        "utilise_la_magie": True,
        "est_un_lyceen": True,
    }


def test_simulate_levi_special_rule():
    attrs = ak.simulate_binary_attributes("Levi Ackerman", "")
    assert attrs["est_le_plus_fort_de_l_humanite"] is True


def test_simulate_handles_none_description():
    assert ak.simulate_binary_attributes("Nobody", None) == {}


# --- run_extraction ------------------------------------------------------


def _patch_paths(mocker, tmp_path, items, existing=None):
    inp = tmp_path / "refined_characters.json"
    out = tmp_path / "akinetix_attributes.json"
    inp.write_text(json.dumps(items), encoding="utf-8")
    if existing is not None:
        out.write_text(json.dumps(existing), encoding="utf-8")
    mocker.patch.object(ak, "INPUT_FILE", str(inp))
    mocker.patch.object(ak, "OUTPUT_FILE", str(out))
    return inp, out


def test_run_extraction_returns_when_input_missing(mocker, tmp_path):
    mocker.patch.object(ak, "INPUT_FILE", str(tmp_path / "missing.json"))
    out = tmp_path / "out.json"
    mocker.patch.object(ak, "OUTPUT_FILE", str(out))
    ak.run_extraction()
    assert not out.exists()


def test_run_extraction_simulation_path_writes_output(mocker, tmp_path):
    """No BRAIN_URL -> simulation attributes computed and written to disk."""
    _, out = _patch_paths(
        mocker,
        tmp_path,
        [
            {"id": 1, "name": "Guts", "biography": "wields a sword"},
            {"id": 2, "name": "Levi", "description": ""},
        ],
    )
    mocker.patch.object(ak, "BRAIN_URL", None)

    ak.run_extraction()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["1"] == {"porte_une_epee": True}
    assert data["2"] == {"est_le_plus_fort_de_l_humanite": True}


def test_run_extraction_skips_already_enriched(mocker, tmp_path):
    """Ids already present in OUTPUT_FILE are not reprocessed."""
    _, out = _patch_paths(
        mocker,
        tmp_path,
        [{"id": 1, "name": "Guts", "biography": "sword"}],
        existing={"1": {"already": True}},
    )
    mocker.patch.object(ak, "BRAIN_URL", None)
    sim = mocker.patch.object(ak, "simulate_binary_attributes")

    ak.run_extraction()

    sim.assert_not_called()
    assert json.loads(out.read_text(encoding="utf-8")) == {"1": {"already": True}}


def test_run_extraction_prefers_llm_then_falls_back(mocker, tmp_path):
    """With BRAIN_URL set, LLM is tried; None result falls back to simulation."""
    _, out = _patch_paths(
        mocker,
        tmp_path,
        [
            {"id": 10, "name": "A", "biography": "magic user"},
            {"id": 11, "name": "B", "biography": "uses a sword"},
        ],
    )
    mocker.patch.object(ak, "BRAIN_URL", "http://brain")
    # First char: LLM returns attrs; second char: LLM returns None -> simulate.
    llm = mocker.patch.object(
        ak,
        "extract_binary_attributes",
        side_effect=[{"llm_attr": True}, None],
    )

    ak.run_extraction()

    assert llm.call_count == 2
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["10"] == {"llm_attr": True}
    assert data["11"] == {"porte_une_epee": True}  # simulated fallback


def test_run_extraction_recovers_from_corrupt_output_file(mocker, tmp_path):
    """A malformed OUTPUT_FILE is logged + ignored; processing still proceeds."""
    inp = tmp_path / "refined_characters.json"
    out = tmp_path / "akinetix_attributes.json"
    inp.write_text(
        json.dumps([{"id": 1, "name": "Guts", "biography": "sword"}]), "utf-8"
    )
    out.write_text("{ this is not valid json", encoding="utf-8")
    mocker.patch.object(ak, "INPUT_FILE", str(inp))
    mocker.patch.object(ak, "OUTPUT_FILE", str(out))
    mocker.patch.object(ak, "BRAIN_URL", None)
    warn = mocker.patch.object(ak.logger, "warning")

    ak.run_extraction()

    assert warn.called
    # Corrupt prior state discarded; fresh attributes written.
    assert json.loads(out.read_text(encoding="utf-8")) == {
        "1": {"porte_une_epee": True}
    }


def test_run_extraction_uses_description_priority(mocker, tmp_path):
    """biography wins over clean_description/description for the prompt source."""
    _patch_paths(
        mocker,
        tmp_path,
        [{"id": 1, "name": "X", "biography": "BIO", "description": "DESC"}],
    )
    mocker.patch.object(ak, "BRAIN_URL", "http://brain")
    llm = mocker.patch.object(ak, "extract_binary_attributes", return_value={"a": True})
    ak.run_extraction()
    # Second positional arg is the description passed to the extractor.
    assert llm.call_args.args[1] == "BIO"
