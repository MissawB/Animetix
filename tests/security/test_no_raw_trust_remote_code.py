"""
Regression-guard: no literal `trust_remote_code=True` is allowed anywhere
under backend/adapters/.

`trust_remote_code=True` executes arbitrary Python from a HuggingFace repo
at load-time.  Any use that must exist should be gated behind an explicit
allow-list env-var so it is off by default in CI and production.

If this test fails, remove the literal and use the project-approved
env-gated helper instead.
"""

import pathlib
import re

ADAPTERS_ROOT = pathlib.Path(__file__).parent.parent.parent / "backend" / "adapters"

PATTERN = re.compile(r"trust_remote_code\s*=\s*True")


def _py_files(root: pathlib.Path):
    return sorted(root.rglob("*.py"))


def test_no_literal_trust_remote_code_in_adapters():
    """
    Scan every .py file under backend/adapters/ and fail if any line
    contains the literal assignment  trust_remote_code=True  (with optional
    whitespace around '=').
    """
    assert (
        ADAPTERS_ROOT.is_dir()
    ), f"backend/adapters/ not found at expected path: {ADAPTERS_ROOT}"

    violations: list[str] = []
    for py_file in _py_files(ADAPTERS_ROOT):
        for lineno, line in enumerate(
            py_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if PATTERN.search(line):
                rel = py_file.relative_to(ADAPTERS_ROOT.parent.parent)
                violations.append(f"{rel}:{lineno}: {line.rstrip()}")

    assert not violations, (
        "Forbidden literal trust_remote_code=True found in backend/adapters/.\n"
        "Use the env-gated allow-list helper instead.\n\n"
        "Violations:\n" + "\n".join(violations)
    )
