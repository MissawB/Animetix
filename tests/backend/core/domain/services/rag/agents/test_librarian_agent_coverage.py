from unittest.mock import MagicMock, patch

from core.domain.services.rag.agents.librarian import LibrarianAgent

MOD = "core.domain.services.rag.agents.librarian"


def _make_agent(generate=None):
    llm = MagicMock()
    pm = MagicMock()
    web = MagicMock()
    pm.get_prompt.return_value = ("LIB_PROMPT", "LIB_SYS")
    if generate is not None:
        llm.generate.side_effect = generate
    return LibrarianAgent(llm, pm, web), llm, pm, web


# --- identify_gap ---------------------------------------------------------


def test_identify_gap_returns_gap_dict():
    raw = 'Sure: {"source_type": "JIKAN", "query": "Naruto"} thanks'
    agent, llm, pm, _ = _make_agent(generate=lambda *a, **k: raw)

    result = agent.identify_gap("q", "ctx")

    assert result == {"source_type": "JIKAN", "query": "Naruto"}
    # SLM path used
    assert llm.generate.call_args.kwargs.get("use_slm") is True
    _, kwargs = pm.get_prompt.call_args
    assert kwargs["query"] == "q"
    assert kwargs["context"] == "ctx"


def test_identify_gap_source_type_none_returns_none():
    raw = '{"source_type": "none", "query": "x"}'
    agent, _, _, _ = _make_agent(generate=lambda *a, **k: raw)
    assert agent.identify_gap("q", "ctx") is None


def test_identify_gap_empty_response_returns_none():
    agent, _, _, _ = _make_agent(generate=lambda *a, **k: "")
    assert agent.identify_gap("q", "ctx") is None


def test_identify_gap_no_source_type_field_returns_none():
    raw = '{"query": "x"}'
    agent, _, _, _ = _make_agent(generate=lambda *a, **k: raw)
    assert agent.identify_gap("q", "ctx") is None


def test_identify_gap_invalid_json_returns_none():
    raw = "{ this is not json }"
    agent, _, _, _ = _make_agent(generate=lambda *a, **k: raw)
    assert agent.identify_gap("q", "ctx") is None


def test_identify_gap_no_braces_returns_none():
    raw = "no json here at all"
    agent, _, _, _ = _make_agent(generate=lambda *a, **k: raw)
    assert agent.identify_gap("q", "ctx") is None


def test_identify_gap_exception_returns_none():
    agent, llm, _, _ = _make_agent()
    llm.generate.side_effect = RuntimeError("boom")
    assert agent.identify_gap("q", "ctx") is None


# --- fetch_data dispatch --------------------------------------------------


def test_fetch_data_no_query_returns_message():
    agent, _, _, _ = _make_agent()
    assert (
        agent.fetch_data({"source_type": "JIKAN"}) == "No query provided for retrieval."
    )


def test_fetch_data_unsupported_source():
    agent, _, _, _ = _make_agent()
    out = agent.fetch_data({"source_type": "MANGA", "query": "x"})
    assert out == "Unsupported source type: MANGA"


def test_fetch_data_routes_to_jikan():
    agent, _, _, _ = _make_agent()
    agent._fetch_from_jikan = MagicMock(return_value="JIKAN_RES")
    out = agent.fetch_data({"source_type": "jikan", "query": "Naruto"})
    assert out == "JIKAN_RES"
    agent._fetch_from_jikan.assert_called_once_with("Naruto")


def test_fetch_data_routes_to_web():
    agent, _, _, _ = _make_agent()
    agent._fetch_from_web = MagicMock(return_value="WEB_RES")
    out = agent.fetch_data({"source_type": "WEB", "query": "Naruto"})
    assert out == "WEB_RES"
    agent._fetch_from_web.assert_called_once_with("Naruto")


# --- _fetch_from_jikan ----------------------------------------------------


def test_fetch_from_jikan_success():
    agent, _, _, _ = _make_agent()
    resp = MagicMock()
    resp.json.return_value = {
        "data": [
            {
                "title": "Naruto",
                "status": "Finished",
                "episodes": 220,
                "score": 8.0,
                "synopsis": "A ninja story." * 50,
            }
        ]
    }
    with patch(f"{MOD}.safe_http_request", return_value=resp) as http:
        out = agent._fetch_from_jikan("Naruto Shippuden")

    assert "RÉSULTATS JIKAN" in out
    assert "Naruto" in out
    assert "8.0/10" in out
    # URL encoded + safe http used
    args, kwargs = http.call_args
    assert args[0] == "GET"
    assert "Naruto%20Shippuden" in args[1]
    resp.raise_for_status.assert_called_once()


def test_fetch_from_jikan_no_results():
    agent, _, _, _ = _make_agent()
    resp = MagicMock()
    resp.json.return_value = {"data": []}
    with patch(f"{MOD}.safe_http_request", return_value=resp):
        out = agent._fetch_from_jikan("Unknown")
    assert "No results found on Jikan" in out


def test_fetch_from_jikan_error():
    agent, _, _, _ = _make_agent()
    with patch(f"{MOD}.safe_http_request", side_effect=RuntimeError("net down")):
        out = agent._fetch_from_jikan("Naruto")
    assert "Error fetching from Jikan" in out
    assert "net down" in out


# --- _fetch_from_web ------------------------------------------------------


def test_fetch_from_web_success_snippet():
    agent, _, _, web = _make_agent()
    web.search.return_value = [
        {"title": "T1", "snippet": "S1", "url": "http://a"},
    ]
    out = agent._fetch_from_web("Naruto")
    assert "RÉSULTATS RECHERCHE WEB" in out
    assert "T1" in out and "S1" in out and "http://a" in out
    web.search.assert_called_once_with("Naruto", limit=5)


def test_fetch_from_web_success_content_fallback_and_defaults():
    agent, _, _, web = _make_agent()
    # no title, no snippet -> uses content fallback and default title
    web.search.return_value = [{"content": "C1"}]
    out = agent._fetch_from_web("Naruto")
    assert "Sans titre" in out
    assert "C1" in out


def test_fetch_from_web_no_results():
    agent, _, _, web = _make_agent()
    web.search.return_value = []
    out = agent._fetch_from_web("Naruto")
    assert "No web search results found" in out


def test_fetch_from_web_error():
    agent, _, _, web = _make_agent()
    web.search.side_effect = RuntimeError("ws fail")
    out = agent._fetch_from_web("Naruto")
    assert "Error fetching from Web" in out
    assert "ws fail" in out
