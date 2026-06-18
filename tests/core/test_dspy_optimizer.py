from unittest.mock import MagicMock

from core.domain.services.dspy_prompt_optimizer import DSPyPromptOptimizer


def test_dspy_optimizer_mutation():
    mock_engine = MagicMock()
    mock_engine.generate.return_value = "Optimized template"
    optimizer = DSPyPromptOptimizer(inference_engine=mock_engine)

    mutated_list = optimizer.mutate_template("Old template")
    # Mutate returns a list of templates including the original
    assert "Optimized template" in mutated_list
    assert "Old template" in mutated_list
    assert mock_engine.generate.call_count >= 1
