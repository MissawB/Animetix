from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import SearchPlan
from core.domain.exceptions import ParsingError
from core.domain.services.rag.agents.planner import SearchPlanner


def _make_planner(generate_structured=None, generate=None):
    llm = MagicMock()
    pm = MagicMock()
    # get_prompt returns (prompt, system_prompt)
    pm.get_prompt.return_value = ("PLAN_PROMPT", "PLAN_SYS")
    if generate_structured is not None:
        llm.generate_structured.side_effect = generate_structured
    if generate is not None:
        llm.generate.side_effect = generate
    return SearchPlanner(llm, pm), llm, pm


# --- Structured (happy) path ---


def test_plan_structured_returns_plan_and_routes_flags():
    plan = SearchPlan(
        optimized_query="Naruto rivals",
        entities=["Naruto"],
        requires_web=True,
        requires_graph=True,
        requires_saga=False,
        graph_traversal_steps=["RIVAL_DE"],
        reasoning="graph + web",
    )
    planner, llm, pm = _make_planner(generate_structured=lambda *a, **k: plan)

    result = planner.plan("Who are Naruto's rivals?", memories="likes shonen")

    assert isinstance(result, SearchPlan)
    assert result.requires_web is True
    assert result.requires_graph is True
    assert result.optimized_query == "Naruto rivals"
    # memories appended to system prompt
    _, kwargs = pm.get_prompt.call_args
    assert kwargs["query"] == "Who are Naruto's rivals?"
    # generate_structured received the augmented system prompt containing memories
    sys_arg = llm.generate_structured.call_args.kwargs["system_prompt"]
    assert "likes shonen" in sys_arg
    # fallback generate() never called on happy path
    llm.generate.assert_not_called()


def test_plan_structured_normalizes_dict_entities_and_steps():
    plan = SearchPlan(
        optimized_query="q",
        entities=[],
        graph_traversal_steps=[],
        reasoning="r",
    )
    # Inject raw dict/list shapes the validator would normally reject; bypass via construct-like set
    plan.entities = [{"name": "Luffy"}, {"value": "Zoro"}, {"foo": "bar"}, "Nami"]
    plan.graph_traversal_steps = [
        {"relation": "ALLY_OF"},
        {"name": "Crew"},
        {"x": 1},
        ["A", "B"],
        "FLAT",
    ]
    planner, _, _ = _make_planner(generate_structured=lambda *a, **k: plan)

    result = planner.plan("q")

    # entities flattened to strings
    assert result.entities[0] == "Luffy"
    assert result.entities[1] == "Zoro"
    assert result.entities[3] == "Nami"
    assert all(isinstance(e, str) for e in result.entities)
    # graph steps flattened, including expansion of the sublist
    assert "ALLY_OF" in result.graph_traversal_steps
    assert "Crew" in result.graph_traversal_steps
    assert "A" in result.graph_traversal_steps
    assert "B" in result.graph_traversal_steps
    assert "FLAT" in result.graph_traversal_steps


# --- Fallback (manual parse) path ---


def test_plan_fallback_parses_fenced_json():
    def boom(*a, **k):
        raise RuntimeError("structured failed")

    raw = """Here is the plan:
```json
{
  "optimized_query": "Goku transformations",
  "entities": [{"name": "Goku"}],
  "requires_web": false,
  "requires_graph": true,
  "graph_traversal_steps": [["TRANSFORMS_INTO"]],
  "reasoning": "graph traversal"
}
```
Done."""
    planner, llm, _ = _make_planner(
        generate_structured=boom, generate=lambda *a, **k: raw
    )

    result = planner.plan("Goku forms?")

    assert isinstance(result, SearchPlan)
    assert result.optimized_query == "Goku transformations"
    assert result.entities == ["Goku"]
    assert result.requires_graph is True
    assert result.graph_traversal_steps == ["TRANSFORMS_INTO"]
    llm.generate.assert_called_once()


def test_plan_fallback_strips_trailing_commas():
    def boom(*a, **k):
        raise RuntimeError("structured failed")

    raw = '{"optimized_query": "q", "entities": ["A",], "reasoning": "r",}'
    planner, _, _ = _make_planner(
        generate_structured=boom, generate=lambda *a, **k: raw
    )

    result = planner.plan("q")
    assert result.optimized_query == "q"
    assert result.entities == ["A"]


def test_plan_fallback_normalizes_dict_entities_and_steps():
    def boom(*a, **k):
        raise RuntimeError("structured failed")

    raw = (
        '{"optimized_query": "q",'
        ' "entities": [{"name": "Luffy"}, {"value": "Zoro"}, {"foo": "x"}, "Nami"],'
        ' "graph_traversal_steps": [{"relation": "ALLY_OF"}, {"name": "Crew"}, {"x": 1}, ["A", "B"], "FLAT"],'
        ' "reasoning": "r"}'
    )
    planner, _, _ = _make_planner(
        generate_structured=boom, generate=lambda *a, **k: raw
    )

    result = planner.plan("q")
    assert result.entities[:2] == ["Luffy", "Zoro"]
    assert "Nami" in result.entities
    assert "ALLY_OF" in result.graph_traversal_steps
    assert "Crew" in result.graph_traversal_steps
    assert "A" in result.graph_traversal_steps and "B" in result.graph_traversal_steps
    assert "FLAT" in result.graph_traversal_steps


def test_plan_fallback_invalid_json_raises_parsing_error():
    def boom(*a, **k):
        raise RuntimeError("structured failed")

    planner, _, _ = _make_planner(
        generate_structured=boom, generate=lambda *a, **k: "not json at all >>>"
    )

    with pytest.raises(ParsingError):
        planner.plan("q")


def test_plan_fallback_non_dict_json_raises_parsing_error():
    def boom(*a, **k):
        raise RuntimeError("structured failed")

    planner, _, _ = _make_planner(
        generate_structured=boom, generate=lambda *a, **k: "[1, 2, 3]"
    )

    with pytest.raises(ParsingError):
        planner.plan("q")
