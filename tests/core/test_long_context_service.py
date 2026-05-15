import pytest
from unittest.mock import MagicMock
from core.domain.services.long_context_service import LongContextDiscoveryService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def long_context_service(mock_engine):
    return LongContextDiscoveryService(inference_engine=mock_engine)

def test_create_haystack(long_context_service):
    haystack = long_context_service.create_haystack("filler", "needle", 100, 0.5)
    assert "needle" in haystack
    assert len(haystack.split()) >= 100

def test_run_needle_test_success(long_context_service, mock_engine):
    mock_engine.generate.return_value = "The code is needle"
    res = long_context_service.run_needle_test("needle", "What is code?", 100, 0.1)
    assert res["success"] is True
    assert res["context_size"] == 100

def test_run_needle_test_failure(long_context_service, mock_engine):
    mock_engine.generate.return_value = "I don't know"
    res = long_context_service.run_needle_test("needle", "Q", 100, 0.5)
    assert res["success"] is False

def test_benchmark_model_limits(long_context_service, mock_engine):
    # Mock must return the needle for success
    mock_engine.generate.return_value = "Le code secret du coffre de Spike Spiegel est 1234."
    results = long_context_service.benchmark_model_limits(sizes=[100, 200])
    # 2 sizes * 3 positions = 6 tests
    assert len(results) == 6
    assert all(r["success"] for r in results)
