"""
Regression-guard: no literal `trust_remote_code=True` is allowed anywhere
under backend/adapters/, backend/pipeline/, or backend/scripts/.

`trust_remote_code=True` executes arbitrary Python from a HuggingFace repo
at load-time.  Any use that must exist should be gated behind an explicit
allow-list env-var so it is off by default in CI and production.

If this test fails, remove the literal and use the project-approved
env-gated helper instead.
"""

import pathlib
import re

BACKEND_ROOT = pathlib.Path(__file__).parent.parent.parent / "backend"

SCAN_ROOTS = [
    BACKEND_ROOT / "adapters",
    BACKEND_ROOT / "pipeline",
    BACKEND_ROOT / "scripts",
]

PATTERN = re.compile(r"trust_remote_code\s*=\s*True")


def _py_files(root: pathlib.Path):
    return sorted(root.rglob("*.py"))


def test_no_literal_trust_remote_code():
    """
    Scan every .py file under backend/adapters/, backend/pipeline/, and
    backend/scripts/ and fail if any line contains the literal assignment
    trust_remote_code=True  (with optional whitespace around '=').
    """
    missing = [str(r) for r in SCAN_ROOTS if not r.is_dir()]
    assert not missing, f"Expected scan roots not found: {missing}"

    violations: list[str] = []
    for root in SCAN_ROOTS:
        for py_file in _py_files(root):
            for lineno, line in enumerate(
                py_file.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if PATTERN.search(line):
                    rel = py_file.relative_to(BACKEND_ROOT.parent)
                    violations.append(f"{rel}:{lineno}: {line.rstrip()}")

    assert not violations, (
        "Forbidden literal trust_remote_code=True found in backend/.\n"
        "Use resolve_trust_remote_code() from core.utils.model_registry instead.\n\n"
        "Violations:\n" + "\n".join(violations)
    )
