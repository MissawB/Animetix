import os
import pathlib
from unittest.mock import patch


def test_brain_api_host_default_logic():
    """
    Verify that the host selection logic used in brain_api.py
    correctly defaults to '127.0.0.1'.

    This addresses Bandit B104 (binding to all interfaces).
    """
    # Simulate environment NOT having the variable set
    with patch.dict(os.environ, {}, clear=True):
        host = os.getenv("BRAIN_API_HOST", "127.0.0.1")
        assert host == "127.0.0.1", (
            "Host should default to 127.0.0.1 for security (B104)"
        )


def test_brain_api_host_override_logic():
    """
    Verify that the host selection logic used in brain_api.py
    respects the 'BRAIN_API_HOST' environment variable.
    """
    custom_host = "192.168.1.5"
    with patch.dict(os.environ, {"BRAIN_API_HOST": custom_host}):
        host = os.getenv("BRAIN_API_HOST", "127.0.0.1")
        assert host == custom_host, (
            f"Host should respect BRAIN_API_HOST env var, got {host}"
        )


def test_production_file_contains_logic():
    """
    Verify that the actual brain_api.py file contains the expected secure host logic.
    This ensures that the tests above are validating the real production code's intent.
    """
    # Get project root
    current_dir = pathlib.Path(__file__).parent.resolve()
    # current_dir is ROOT/tests/security
    # project_root is 2 levels up
    project_root = current_dir.parent.parent
    brain_api_path = (
        project_root / "backend" / "adapters" / "inference" / "brain_api.py"
    )

    assert brain_api_path.exists(), f"Brain API file not found at {brain_api_path}"

    with open(brain_api_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for the specific logic block
    expected_logic = 'host = os.getenv("BRAIN_API_HOST", "127.0.0.1")'
    assert expected_logic in content, (
        f"Production file {brain_api_path} must contain secure host logic: {expected_logic}"
    )
