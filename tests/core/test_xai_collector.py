from core.domain.services.xai_service import XaiCollector


def test_xai_collector_initialization():
    collector = XaiCollector()
    assert collector.steps == []
    assert collector.retrieved_docs == []
    assert collector.intent == ""


def test_log_intent():
    collector = XaiCollector()
    collector.log_intent("User wants to find anime about cooking.")
    assert collector.intent == "User wants to find anime about cooking."


def test_log_retrieval():
    collector = XaiCollector()
    docs = [
        {"id": "1", "title": "Food Wars!", "score": 0.9},
        {"id": "2", "title": "Yakitate!! Japan", "score": 0.8},
    ]
    collector.log_retrieval(docs)
    assert collector.retrieved_docs == docs


def test_log_agent_thought():
    collector = XaiCollector()
    collector.log_agent_thought("Planner", "I will search for cooking anime.")
    collector.log_agent_thought("Researcher", "Found several matches.")

    assert len(collector.steps) == 2
    assert collector.steps[0] == {
        "agent": "Planner",
        "thought": "I will search for cooking anime.",
    }
    assert collector.steps[1] == {
        "agent": "Researcher",
        "thought": "Found several matches.",
    }
