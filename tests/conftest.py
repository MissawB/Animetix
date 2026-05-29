import sys
import os
from importlib.abc import MetaPathFinder, Loader
import importlib
from importlib.machinery import ModuleSpec

class AliasLoader(Loader):
    def __init__(self, real_module):
        self.real_module = real_module

    def create_module(self, spec):
        return self.real_module

    def exec_module(self, module):
        pass

class SrcPipelineMapper(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("src.pipeline"):
            real_name = fullname.replace("src.pipeline", "pipeline", 1)
            try:
                mod = importlib.import_module(real_name)
                spec = ModuleSpec(fullname, AliasLoader(mod))
                return spec
            except Exception:
                pass
        return None

sys.meta_path.insert(0, SrcPipelineMapper())

# Map the parent packages
try:
    import src
except ImportError:
    import types
    src = types.ModuleType("src")
    sys.modules["src"] = src

try:
    import pipeline
    src.pipeline = pipeline
    sys.modules["src.pipeline"] = pipeline
except Exception:
    pass

import pytest
import tracemalloc
def create_image_bytes(width: int = 256, height: int = 256, mode: str = "RGB", fmt: str = "JPEG") -> bytes:
    """Create an image in memory and return its bytes.
    Used by test fixtures to avoid filesystem I/O.
    """
    from io import BytesIO
    from PIL import Image
    img = Image.new(mode, (width, height), color=(73, 109, 137))
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()
from unittest.mock import MagicMock

@pytest.fixture(scope="session", autouse=True)
def enable_tracemalloc():
    """Enable tracemalloc for the entire test session to silence resource warnings."""
    tracemalloc.start()
    yield
    tracemalloc.stop()

@pytest.fixture

def sample_image():
    """Return JPEG bytes of a 256x256 RGB image for tests.
    Uses the helper to keep image creation logic in one place.
    """
    return create_image_bytes(width=256, height=256, mode="RGB", fmt="JPEG")

@pytest.fixture
def mock_pipeline():
    """Provide a generic mocked pipeline that returns a depth Image.
    Used by both DiffusersAdapter and VisionTransformersAdapter tests.
    """
    pipeline = MagicMock()
    dummy_depth = MagicMock()
    # Create a simple grayscale image for depth
    from PIL import Image
    dummy_depth_image = Image.new('L', (256, 256), color=128)
    pipeline.return_value = {"depth": dummy_depth_image}
    return pipeline

@pytest.fixture
def mock_container():
    """Generic mock container for dependency injection tests."""
    container = MagicMock()
    # Mock services commonly used in tests
    container.inference_engine = MagicMock()
    container.prompt_manager = MagicMock()
    container.llm_service = MagicMock()
    container.agentic_rag = MagicMock()
    container.graph_persistence_port = MagicMock()
    container.visual_novel_service = MagicMock()
    container.video_quest_service = MagicMock()
    container.catalog_service = MagicMock()
    container.red_teaming_agent = MagicMock()
    return container
