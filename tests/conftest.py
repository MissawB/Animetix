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


@pytest.fixture(scope="session", autouse=True)
def _preload_urlconf():
    """Charge l'URLConf (donc tous les modules de vues) AVANT le premier
    snapshot de ``_cleanup_module_pollution``.

    Sans ça, l'URLConf se charge paresseusement pendant le premier test qui
    fait un ``reverse()`` : ses modules de vues sont purgés au teardown alors
    que le résolveur d'URLs Django (persistant) garde les fonctions de
    l'ancienne instance. Un ``patch("animetix.xxx.yyy")`` ultérieur ré-importe
    une seconde instance et patche la mauvaise (split-brain) — vu en CI le
    2026-07-10 sur test_eventarc_gcs_upload_endpoint_success.
    """
    from django.urls import get_resolver

    get_resolver().url_patterns


@pytest.fixture(autouse=True)
def _cleanup_module_pollution():
    """Garde-fou anti-pollution entre tests (défense en profondeur).

    Snapshot/restore complet de ``sys.modules`` : tout module ajouté, remplacé
    ou supprimé pendant le test est restauré à l'identique. Cela couvre les
    ``MagicMock``, les ``types.ModuleType`` fakes, les sentinelles ``None``, et
    les remplacements de vrais modules — là où l'ancien garde ne détectait que
    les instances de ``Mock``.
    """
    snapshot = dict(sys.modules)
    yield
    # Modules with irreversible import-time global registration must never be
    # purged: deleting them forces a re-import that duplicate-registers and
    # crashes unrelated later tests. numba registers PolynomialType (and other
    # numpy types) into a process-global type registry on import; llvmlite holds
    # native LLVM bindings. Keep them pinned once imported.
    _unpurgeable = ("numba", "llvmlite")
    # Remove any module added during the test
    for name in set(sys.modules) - set(snapshot):
        if name.startswith(_unpurgeable):
            continue
        del sys.modules[name]
    # Restore any module that was replaced or deleted during the test
    for name, mod in snapshot.items():
        if sys.modules.get(name) is not mod:
            sys.modules[name] = mod
    try:
        from core.utils.lazy_import import _loaded_modules

        _loaded_modules.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Clear the Django cache before each test.

    DRF throttles (``CpuGameThrottle``, ``BurstAnonRateThrottle``, ...) keep
    their request counters in the default cache (LocMemCache in tests). Without
    a reset, counters accumulate across tests and cause spurious 429s in tests
    that don't expect throttling.
    """
    from django.core.cache import cache

    cache.clear()
    yield


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
    # MagicMock auto-creates the nested sub-container paths on access
    # (container.core.x, container.agentic.y, ...); configure per-test.
    return container
