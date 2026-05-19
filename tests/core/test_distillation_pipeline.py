import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_teacher():
    return MagicMock()

@pytest.fixture
def mock_prompt_manager():
    manager = MagicMock()
    manager.get_prompt.return_value = ("Formatted Prompt", "System Prompt")
    return manager

def test_generate_distillation_data(mock_teacher, mock_prompt_manager):
    from core.domain.services.distillation_pipeline import ModelDistillationPipeline
    distillation_pipeline = ModelDistillationPipeline(teacher_engine=mock_teacher, prompt_manager=mock_prompt_manager)
    mock_teacher.generate.return_value = "Knowledge"
    data = distillation_pipeline.generate_distillation_data(["Naruto"])
    
    mock_prompt_manager.get_prompt.assert_called_once_with("distillation_explanation", topic="Naruto")
    
    assert len(data) == 1
    assert data[0]["output"] == "Knowledge"

def test_fine_tune_student(mock_teacher, mock_prompt_manager):
    pytest.importorskip("datasets")
    from core.domain.services.distillation_pipeline import ModelDistillationPipeline
    distillation_pipeline = ModelDistillationPipeline(teacher_engine=mock_teacher, prompt_manager=mock_prompt_manager)
    # ...
