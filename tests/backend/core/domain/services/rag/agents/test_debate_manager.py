import json
from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import DebateOutcome, JudgeAction
from core.domain.exceptions import InferenceError
from core.domain.services.rag.agents.debate_manager import (
    DebateManager,
    robust_json_loads,
    sanitize_judge_data,
)

# --- robust_json_loads ---


def test_robust_json_loads_plain():
    assert robust_json_loads('{"a": 1}') == {"a": 1}


def test_robust_json_loads_fenced():
    raw = 'prefix ```json\n{"a": 2}\n``` suffix'
    assert robust_json_loads(raw) == {"a": 2}


def test_robust_json_loads_recovers_trailing_comma_and_comments():
    raw = '{"a": 1, // note\n "b": 2,}'
    assert robust_json_loads(raw) == {"a": 1, "b": 2}


def test_robust_json_loads_unrecoverable_raises():
    with pytest.raises(ValueError):
        robust_json_loads("definitely not json {{{")


# --- sanitize_judge_data ---


def test_sanitize_maps_action_synonyms():
    assert (
        sanitize_judge_data({"next_action": "yes"})["next_action"]
        == JudgeAction.APPROVE
    )
    assert (
        sanitize_judge_data({"next_action": "please REPLAN now"})["next_action"]
        == JudgeAction.REPLAN
    )
    assert (
        sanitize_judge_data({"next_action": "research more"})["next_action"]
        == JudgeAction.RESEARCH_MORE
    )
    assert (
        sanitize_judge_data({"next_action": "rewrite it"})["next_action"]
        == JudgeAction.REWRITE
    )
    # unknown -> default REWRITE
    assert (
        sanitize_judge_data({"next_action": "garbage"})["next_action"]
        == JudgeAction.REWRITE
    )


def test_sanitize_clamps_scores():
    d = sanitize_judge_data(
        {"next_action": "APPROVE", "faithfulness_score": 5, "relevancy_score": -3}
    )
    assert d["faithfulness_score"] == 1.0
    assert d["relevancy_score"] == 0.0


def test_sanitize_bad_score_defaults_zero():
    d = sanitize_judge_data({"next_action": "APPROVE", "faithfulness_score": "abc"})
    assert d["faithfulness_score"] == 0.0


def test_sanitize_hallucination_and_reliability_defaults():
    # no hallucination flag -> defaults True (pessimistic); no is_reliable -> derived
    d = sanitize_judge_data({"next_action": "APPROVE", "faithfulness_score": 0.9})
    assert d["hallucination_detected"] is True
    assert d["is_reliable"] is False  # hallucination True => not reliable

    d2 = sanitize_judge_data(
        {
            "next_action": "APPROVE",
            "faithfulness_score": 0.9,
            "hallucination_detected": "false",
        }
    )
    assert d2["hallucination_detected"] is False
    assert d2["is_reliable"] is True  # no hallucination + faithfulness > 0.5


def test_sanitize_string_is_reliable():
    d = sanitize_judge_data(
        {
            "next_action": "APPROVE",
            "hallucination_detected": "false",
            "is_reliable": "TRUE",
        }
    )
    assert d["is_reliable"] is True


def test_sanitize_default_reasoning():
    d = sanitize_judge_data({"next_action": "APPROVE"})
    assert d["reasoning"] == "No reasoning provided by the judge."


# --- DebateManager.conduct_debate ---


def _judge_json(action="APPROVE", faith=0.9, hall=False, reasoning="ok"):
    return json.dumps(
        {
            "next_action": action,
            "faithfulness_score": faith,
            "relevancy_score": 0.8,
            "hallucination_detected": hall,
            "reasoning": reasoning,
            "is_reliable": True,
        }
    )


def _make_manager(generate_side_effect):
    # side_effect may be a callable or a list; MagicMock advances list side_effects
    # under its own lock, which is safe across the debate's worker threads.
    llm = MagicMock()
    llm.generate.side_effect = generate_side_effect
    pm = MagicMock()
    pm.get_prompt.return_value = ("PROMPT", "SYS")
    return DebateManager(llm, pm), llm, pm


def test_conduct_debate_all_approve():
    manager, llm, _ = _make_manager(lambda *a, **k: _judge_json("APPROVE"))

    outcome = manager.conduct_debate("q", "ctx", "answer")

    assert isinstance(outcome, DebateOutcome)
    assert outcome.consensus_action == JudgeAction.APPROVE
    assert len(outcome.critiques) == 3
    assert llm.generate.call_count == 3


def test_conduct_debate_pessimistic_replan_wins():
    # Two approve, one replan -> REPLAN has highest priority (order-independent)
    manager, _, _ = _make_manager(
        [_judge_json("APPROVE"), _judge_json("REPLAN"), _judge_json("REWRITE")]
    )
    outcome = manager.conduct_debate("q", "ctx", "answer")
    assert outcome.consensus_action == JudgeAction.REPLAN


def test_conduct_debate_research_beats_rewrite():
    manager, _, _ = _make_manager(
        [_judge_json("APPROVE"), _judge_json("RESEARCH_MORE"), _judge_json("REWRITE")]
    )
    outcome = manager.conduct_debate("q", "ctx", "answer")
    assert outcome.consensus_action == JudgeAction.RESEARCH_MORE


def test_conduct_debate_all_fail_defaults_rewrite():
    def fail(*a, **k):
        raise InferenceError("engine down")

    manager, _, _ = _make_manager(fail)
    outcome = manager.conduct_debate("q", "ctx", "answer")

    assert outcome.consensus_action == JudgeAction.REWRITE
    assert outcome.critiques == {}
    assert "Debate failed" in outcome.final_reasoning


def test_conduct_debate_partial_failures_still_decides():
    # Two judges return garbage (None), one returns a valid REWRITE
    manager, _, _ = _make_manager(
        ["garbage {{{", _judge_json("REWRITE"), "also bad <<<"]
    )
    outcome = manager.conduct_debate("q", "ctx", "answer")

    assert outcome.consensus_action == JudgeAction.REWRITE
    assert len(outcome.critiques) == 1


def test_conduct_debate_thinking_mode_splits_budget():
    captured = []

    def capture(*a, **k):
        captured.append(k.get("thinking_budget"))
        return _judge_json("APPROVE")

    manager, _, _ = _make_manager(capture)
    manager.conduct_debate(
        "q", "ctx", "answer", thinking_budget=300, thinking_mode=True
    )

    # 300 budget split across 3 judges = 100 each
    assert captured == [100, 100, 100]


def test_conduct_debate_logs_to_xai_collector():
    collector = MagicMock()
    manager, _, _ = _make_manager(lambda *a, **k: _judge_json("APPROVE"))
    manager.conduct_debate("q", "ctx", "answer", xai_collector=collector)
    collector.log_agent_thought.assert_called_once()
    args = collector.log_agent_thought.call_args.args
    assert args[0] == "DebateManager"
