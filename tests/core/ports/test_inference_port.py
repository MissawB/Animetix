import pytest
from backend.core.ports.inference_port import (
    InferencePort,
    InferenceNotImplementedError,
)


def test_inference_port_abstract():
    with pytest.raises(TypeError):
        InferencePort()


def test_inference_port_optional_methods():
    class MockAdapter(InferencePort):
        def generate(self, *args, **kwargs):
            pass

        def stream_generate(self, *args, **kwargs):
            pass

        def get_text_embedding(self, *args, **kwargs):
            pass

        def health_check(self, *args, **kwargs):
            pass

    adapter = MockAdapter()
    with pytest.raises(InferenceNotImplementedError):
        adapter.generate_image("test")


def test_inference_port_mandatory_methods():
    class IncompleteAdapter(InferencePort):
        def health_check(self, *args, **kwargs):
            pass

        # generate, stream_generate, get_text_embedding are missing

    # Currently this will NOT raise TypeError because they are not @abstractmethod yet
    with pytest.raises(TypeError):
        IncompleteAdapter()
