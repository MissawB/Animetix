import pytest
import numpy as np
from backend.core.domain.services.scoring_service import ScoringDomainService

def test_calculate_animetix_ragas_score():
    metrics = {'faithfulness': 0.8, 'answer_relevancy': 0.9, 'context_recall': 1.0}
    score = ScoringDomainService.calculate_animetix_ragas_score(metrics)
    assert score == 8.9  # (0.8*0.4 + 0.9*0.3 + 1.0*0.3) * 10 = (0.32 + 0.27 + 0.30)*10 = 8.9

def test_get_gaussian_weights():
    weights = ScoringDomainService.get_gaussian_weights(3)
    assert len(weights) == 3
    assert weights[1] > weights[0] # mu is 1.2, so index 1 is closer to peak

def test_get_ui_score_color_class():
    assert ScoringDomainService.get_ui_score_color_class(95) == "danger"
    assert ScoringDomainService.get_ui_score_color_class(75) == "warning"
    assert ScoringDomainService.get_ui_score_color_class(50) == "primary"
    assert ScoringDomainService.get_ui_score_color_class(20) == "secondary"
