"""Tripwire: no ``provider.reset_override()`` statements in tests.

``reset_override()`` clears the provider's WHOLE overriding stack. On
DependenciesContainer-bound providers (e.g. the ``core.guardrail_service`` →
``agentic.guardrail_service`` alias) the sub-container binding itself lives on
that stack, so a bare ``reset_override()`` detaches it and every later test
resolving through the alias dies with ``Dependency ... is not defined``
(order-dependent, CI-only breakage — bitten on 2026-07-10).

Pop only your own override instead: ``provider.reset_last_overriding()`` in a
``finally``, or better, scope the override with ``with provider.override(...):``.
"""

import re
from pathlib import Path

_STATEMENT = re.compile(r"^\s*[\w.\[\]()\"']+\.reset_override\(\)\s*$")


def test_no_reset_override_statements_in_tests():
    tests_root = Path(__file__).parent
    offenders = []
    for path in tests_root.rglob("*.py"):
        if path.name == Path(__file__).name or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if _STATEMENT.match(line):
                offenders.append(f"{path.relative_to(tests_root)}:{lineno}")
    assert not offenders, (
        "reset_override() clears the whole overriding stack and detaches "
        "DependenciesContainer bindings. Use reset_last_overriding() or a "
        "scoped `with provider.override(...):` block instead:\n  "
        + "\n  ".join(offenders)
    )
