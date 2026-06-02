import pytest
from adapters.persistence.django_eval_adapter import DjangoEvalAdapter
from animetix.models import AIREvalResult

@pytest.mark.django_db
def test_django_eval_adapter_save_result():
    adapter = DjangoEvalAdapter()
    
    # Save a normal result (no hallucination)
    adapter.save_result(
        query="Quel est le rival de Naruto ?",
        context="Naruto a pour rival Sasuke Uchiha.",
        answer="Sasuke Uchiha.",
        metrics={
            "faithfulness": 0.95,
            "answer_relevance": 0.9,
            "context_precision": 0.8,
            "hallucination": False
        }
    )
    
    # Assert entry is saved in DB with correct values
    saved = AIREvalResult.objects.first()
    assert saved is not None
    assert saved.game_mode == "classic"
    assert "Query: Quel est le rival de Naruto ?" in saved.input_context
    assert "Context: Naruto a pour rival Sasuke Uchiha." in saved.input_context
    assert saved.output_text == "Sasuke Uchiha."
    assert saved.faithfulness == 0.95
    assert saved.relevancy == 0.9
    assert saved.precision == 0.8
    assert saved.hallucination_detected is False

@pytest.mark.django_db
def test_django_eval_adapter_get_evaluation_stats():
    adapter = DjangoEvalAdapter()
    
    # Save first entry (no hallucination)
    adapter.save_result(
        query="q1",
        context="c1",
        answer="a1",
        metrics={
            "faithfulness": 0.8,
            "answer_relevance": 0.8,
            "context_precision": 0.8,
            "hallucination": False
        }
    )
    
    # Save second entry (with hallucination)
    adapter.save_result(
        query="q2",
        context="c2",
        answer="a2",
        metrics={
            "faithfulness": 0.4,
            "answer_relevance": 0.6,
            "context_precision": 0.4,
            "hallucination": True
        }
    )
    
    # Check total count
    assert AIREvalResult.objects.count() == 2
    
    # Fetch stats
    stats_data = adapter.get_evaluation_stats()
    
    stats = stats_data["stats"]
    assert stats["total"] == 2
    assert pytest.approx(stats["avg_faith"]) == 0.6
    assert pytest.approx(stats["avg_rel"]) == 0.7
    assert pytest.approx(stats["avg_prec"]) == 0.6
    assert stats_data["hallucination_count"] == 1
