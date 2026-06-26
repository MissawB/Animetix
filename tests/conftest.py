import asyncio
import os
import sys

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# BrainAPIAdapter.__init__ raises ConfigurationError when BRAIN_API_URL is unset
# (it is required — no sensible local default). The DI fallback chain constructs
# every adapter eagerly, so any test that builds the inference chain needs a
# syntactically-valid dummy URL; no real HTTP is performed at construction.
# setdefault keeps a real value (dev .env / CI secret) when one is provided.
os.environ.setdefault("BRAIN_API_URL", "http://localhost:5000")

if sys.platform == "win32":
    # Fail-fast : on impose la Proactor loop et on laisse toute erreur remonter,
    # plutôt que de la masquer silencieusement (ce qui ferait tourner la suite sur
    # la mauvaise policy d'event-loop → pollution async difficile à diagnostiquer).
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import importlib  # noqa: E402
from importlib.abc import Loader, MetaPathFinder  # noqa: E402
from importlib.machinery import ModuleSpec  # noqa: E402


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
    import src  # noqa: E402
except ImportError:
    import types  # noqa: E402

    src = types.ModuleType("src")
    sys.modules["src"] = src

try:
    import pipeline  # noqa: E402

    src.pipeline = pipeline
    sys.modules["src.pipeline"] = pipeline
except Exception:
    pass

import tracemalloc  # noqa: E402

import pytest  # noqa: E402


def _llm_backend_reachable() -> bool:
    """True si le backend LLM (ollama via ``LLM_API_BASE``) accepte une connexion TCP.

    Permet de *skipper* (au lieu d'échouer durement) les tests
    ``@pytest.mark.integration`` qui exigent un LLM live, quand celui-ci est absent
    (CI sans ollama, dev hors-ligne).
    """
    import socket  # noqa: E402
    from urllib.parse import urlparse  # noqa: E402

    base = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    parsed = urlparse(base)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 11434)
    try:
        with socket.create_connection((host, port), timeout=0.75):
            return True
    except OSError:
        return False


def pytest_collection_modifyitems(config, items):
    """Skip gracieux des tests ``integration`` si le backend LLM est injoignable.

    La CI unitaire les exclut déjà via ``-m "not integration"`` ; ce hook permet en
    plus de lancer la suite **complète** n'importe où (et le job CI d'intégration
    non-bloquant) sans échec dur quand ollama n'est pas démarré.
    """
    if _llm_backend_reachable():
        return
    skip_integration = pytest.mark.skip(
        reason="LLM backend (ollama @ LLM_API_BASE) injoignable — test d'intégration skippé"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


def create_image_bytes(
    width: int = 256, height: int = 256, mode: str = "RGB", fmt: str = "JPEG"
) -> bytes:
    """Create an image in memory and return its bytes.
    Used by test fixtures to avoid filesystem I/O.
    """
    from io import BytesIO  # noqa: E402

    from PIL import Image  # noqa: E402

    img = Image.new(mode, (width, height), color=(73, 109, 137))
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


from unittest.mock import MagicMock  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def enable_tracemalloc():
    """Enable tracemalloc for the entire test session to silence resource warnings."""
    tracemalloc.start()
    yield
    tracemalloc.stop()


@pytest.fixture(autouse=True)
def _cleanup_module_pollution():
    """Garde-fou anti-pollution entre tests (défense en profondeur).

    Certains tests injectent des mocks dans ``sys.modules`` (ex. mocker une dépendance
    lourde non installée) ; s'ils ne sont pas restaurés, ils cassent les tests suivants
    qui importent la vraie dépendance. Après chaque test, on retire les modules de type
    ``Mock`` ajoutés pendant le test et on vide le cache de ``lazy_import`` afin
    qu'aucun mock ne persiste.
    """
    from unittest.mock import Mock

    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        if isinstance(sys.modules.get(name), Mock):
            del sys.modules[name]
    try:
        from core.utils.lazy_import import _loaded_modules

        _loaded_modules.clear()
    except Exception:
        pass


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
    MagicMock()
    # Create a simple grayscale image for depth
    from PIL import Image  # noqa: E402

    dummy_depth_image = Image.new("L", (256, 256), color=128)
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
