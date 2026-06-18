from unittest.mock import MagicMock, patch

import pytest
from core.domain.services.multi_lora_manager import MultiLoraManager


# We must ensure PeftModel is seen as a type for isinstance checks
class MockPeftModel:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        # Returns an instance that has load_adapter
        instance = MagicMock()
        instance.load_adapter = MagicMock()
        return instance

    def disable_adapter(self):
        m = MagicMock()
        m.__enter__ = lambda x: None
        m.__exit__ = lambda x, y, z, t: None
        return m

    def set_adapter(self, name):
        pass

    def generate(self, *args, **kwargs):
        return [1]


@pytest.fixture
def mock_model():
    return MagicMock()


@pytest.fixture
def lora_manager(mock_model):
    # Patch at module level
    with patch("core.domain.services.multi_lora_manager.PeftModel", MockPeftModel):
        return MultiLoraManager(base_model=mock_model)


def test_load_adapter_path_not_found(lora_manager):
    lora_manager.load_adapter("test", "/invalid/path")
    assert "test" not in lora_manager.loaded_adapters


def test_load_adapter_success(lora_manager, tmp_path):
    adapter_path = tmp_path / "adapter"
    adapter_path.mkdir()

    with patch("core.domain.services.multi_lora_manager.PeftModel", MockPeftModel):
        # We simulate the base_model being a PeftModel
        lora_manager.base_model = MockPeftModel.from_pretrained()

        # We need to bypass the isinstance check again if it fails
        with patch(
            "core.domain.services.multi_lora_manager.isinstance", return_value=True
        ):
            lora_manager.load_adapter("style_a", str(adapter_path))
            assert "style_a" in lora_manager.loaded_adapters


def test_disable_adapters(lora_manager):
    # Setup base_model as a mock that satisfies isinstance if we patch it
    mock_peft = MagicMock()
    mock_peft.disable_adapter.return_value.__enter__ = lambda x: None
    mock_peft.disable_adapter.return_value.__exit__ = lambda x, y, z, t: None

    lora_manager.base_model = mock_peft
    lora_manager.active_adapter = "a"

    with patch("core.domain.services.multi_lora_manager.isinstance", return_value=True):
        lora_manager.disable_adapters()
        assert lora_manager.active_adapter is None
        mock_peft.disable_adapter.assert_called_once()


def test_load_adapter_exception(lora_manager, tmp_path):
    path = tmp_path / "err"
    path.mkdir()
    # Path the class method
    with patch.object(
        MockPeftModel, "from_pretrained", side_effect=Exception("Load error")
    ):
        with patch("core.domain.services.multi_lora_manager.PeftModel", MockPeftModel):
            lora_manager.load_adapter("fail", str(path))
            assert "fail" not in lora_manager.loaded_adapters
