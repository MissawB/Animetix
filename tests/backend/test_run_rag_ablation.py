from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command


def _fake_container():
    rag = MagicMock()
    rag.generate_advanced_answer_with_context.return_value = ("ans", "ctx")
    judge = MagicMock()
    judge.evaluate_response.return_value = {
        "faithfulness": 0.8,
        "answer_relevancy": 0.8,
        "context_precision": 0.8,
    }
    container = MagicMock()
    container.agentic.rag_service.return_value = rag
    container.core.ragas_eval_service.return_value = judge
    return container, rag, judge


@patch("animetix.management.commands.run_rag_ablation.get_container")
def test_ablation_runs_pipeline_on_and_off(mock_gc):
    container, rag, _ = _fake_container()
    mock_gc.return_value = container
    out = StringIO()
    call_command("run_rag_ablation", "--source", "curated", "--limit", "1", stdout=out)

    modes = [c.args[0] for c in rag.set_cognitive_boosters.call_args_list]
    assert False in modes and True in modes  # both ablation arms run
    assert rag.generate_advanced_answer_with_context.call_count == 2  # ON + OFF
    assert "Verdict" in out.getvalue()


@patch("animetix.management.commands.run_rag_ablation.get_container")
def test_ablation_skips_failing_query(mock_gc):
    container, rag, _ = _fake_container()
    rag.generate_advanced_answer_with_context.side_effect = RuntimeError(
        "pipeline down"
    )
    mock_gc.return_value = container
    out = StringIO()
    call_command("run_rag_ablation", "--source", "curated", "--limit", "1", stdout=out)
    assert "skipped 1" in out.getvalue()
