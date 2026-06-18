from unittest.mock import MagicMock

import pytest
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int


def test_fallback_generate_structured_success():
    mock_adapter1 = MagicMock()
    mock_adapter1.generate_structured.side_effect = Exception("Failed")

    mock_adapter2 = MagicMock()
    mock_user = User(name="Test User", age=25)
    mock_adapter2.generate_structured.return_value = mock_user

    fallback = FallbackInferenceAdapter(adapters=[mock_adapter1, mock_adapter2])

    result = fallback.generate_structured(
        prompt="Extract user info", response_model=User
    )

    assert result == mock_user
    mock_adapter1.generate_structured.assert_called_once()
    mock_adapter2.generate_structured.assert_called_once()


def test_fallback_generate_structured_all_failed():
    mock_adapter1 = MagicMock()
    mock_adapter1.generate_structured.side_effect = Exception("Failed 1")

    mock_adapter2 = MagicMock()
    mock_adapter2.generate_structured.side_effect = Exception("Failed 2")

    fallback = FallbackInferenceAdapter(adapters=[mock_adapter1, mock_adapter2])

    with pytest.raises(Exception) as excinfo:
        fallback.generate_structured(prompt="Extract user info", response_model=User)

    assert "Tous les adaptateurs ont échoué" in str(excinfo.value)


from core.ports.inference_port import InferencePort  # noqa: E402


class MockCapableAdapter(InferencePort):
    def estimate_depth(self, image_data: bytes) -> bytes:
        return b"depth_map"

    def health_check(self) -> dict:
        return {"status": "online"}


class MockGenericAdapter(InferencePort):
    def health_check(self) -> dict:
        return {"status": "online"}


def test_fallback_introspection_capability_mapping():
    adapter1 = MockGenericAdapter()
    adapter2 = MockCapableAdapter()
    fallback = FallbackInferenceAdapter(adapters=[adapter1, adapter2])

    # Introspection checks
    assert fallback._is_method_overridden(adapter2, "estimate_depth") is True
    assert fallback._is_method_overridden(adapter1, "estimate_depth") is False

    # Capability cache verification
    capable = fallback._capability_cache.get("estimate_depth", [])
    assert adapter2 in capable
    assert adapter1 not in capable


def test_fallback_call_routes_directly_to_capable_adapters():
    adapter1 = MockGenericAdapter()
    # Mocking standard Port methods that generic adapter should not execute
    adapter1.estimate_depth = MagicMock(side_effect=Exception("Should not be called"))

    adapter2 = MockCapableAdapter()
    adapter2.estimate_depth = MagicMock(return_value=b"correct_depth")

    fallback = FallbackInferenceAdapter(adapters=[adapter1, adapter2])

    result = fallback.estimate_depth(b"sample_image")

    assert result == b"correct_depth"
    adapter1.estimate_depth.assert_not_called()
    adapter2.estimate_depth.assert_called_once_with(b"sample_image")


from unittest.mock import patch  # noqa: E402

from core.ports.inference_port import InferenceNotImplementedError  # noqa: E402


def test_not_implemented_exception_is_silent_and_does_not_log_error():
    mock_obs = MagicMock()

    adapter1 = MockCapableAdapter()
    adapter1.estimate_depth = MagicMock(
        side_effect=InferenceNotImplementedError("Dynamic override disabled")
    )

    adapter2 = MockCapableAdapter()
    adapter2.estimate_depth = MagicMock(return_value=b"correct_depth_2")

    fallback = FallbackInferenceAdapter(
        adapters=[adapter1, adapter2], obs_service=mock_obs
    )

    with patch("adapters.inference.fallback_adapter.logger.error") as mock_log_err:
        result = fallback.estimate_depth(b"sample_image")

        assert result == b"correct_depth_2"
        # Verify NO error log was written and NO observability error was recorded for the NotImplemented event
        mock_log_err.assert_not_called()
        mock_obs.log_error.assert_not_called()
