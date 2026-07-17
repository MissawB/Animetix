import sys
from importlib.machinery import ModuleSpec
from unittest.mock import MagicMock, patch

import pytest

# Mock heavy/optional modules for environment independence.
mock_diffusers = MagicMock()
mock_pil = MagicMock()
mock_diffusers.__spec__ = ModuleSpec("diffusers", loader=None)
mock_pil.__spec__ = ModuleSpec("PIL", loader=None)

# NOTE: the adapter and its mixin import diffusers/PIL lazily, so we install the
# mocks ONLY for the duration of each test via patch.dict (see below). Installing
# them at module import time would leak into sys.modules during pytest's
# collection phase and break other test modules that need the real PIL/diffusers.
from adapters.inference.diffusers_adapter import DiffusersAdapter  # noqa: E402


@pytest.fixture(autouse=True)
def _mock_heavy_modules(monkeypatch):
    # Install the mocks for the duration of the test only, touching just these
    # two keys so we don't disturb modules (e.g. torch) imported during the test.
    # `monkeypatch.setitem` restores the previous value (or removes the key if it
    # was absent) at teardown, even on error — no raw `sys.modules[...] =` that
    # leaks into later test modules when a restore is missed. This is the leak the
    # global `_cleanup_module_pollution` snapshot in conftest was backstopping.
    monkeypatch.setitem(sys.modules, "diffusers", mock_diffusers)
    monkeypatch.setitem(sys.modules, "PIL", mock_pil)
    yield


@pytest.fixture(autouse=True)
def mock_cuda_available():
    with patch("torch.cuda.is_available", return_value=True):
        yield


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    # Mock the __call__ return value to have images[0]
    mock_image = MagicMock()
    mock_result = MagicMock()
    mock_result.images = [mock_image]
    pipeline.return_value = mock_result

    mock_diffusers.AutoPipelineForText2Image.from_pretrained.return_value = pipeline
    return pipeline


def test_generate_image_success(mock_pipeline):
    adapter = DiffusersAdapter(model_id="test/model")

    # Run generation
    # On mock l'encodage base64 pour éviter PIL.Image
    with patch("base64.b64encode") as mock_b64:
        mock_b64.return_value = b"fake_base64"
        result = adapter.generate_image("A futuristic city", "Cyberpunk")

    # Assertions
    assert result.startswith("data:image/jpeg;base64,")
    # Verify pipeline was called
    mock_pipeline.assert_called_once()
    args, kwargs = mock_pipeline.call_args
    assert "A futuristic city, Cyberpunk" in kwargs["prompt"]


def test_health_check(mock_pipeline):
    adapter = DiffusersAdapter(model_id="test/model")
    # Trigger load
    with patch("base64.b64encode"):
        adapter.generate_image("test")

    health = adapter.health_check()
    assert health["status"] == "online"
    assert health["engine"] == "diffusers"
    assert health["model"] == "test/model"
