"""Proves the games conftest's tripwire actually catches a leaked
``proximity_service`` override.

``conftest.py``'s ``_default_proximity_service`` fixture pushes a harmless stub
via ``with container.core.proximity_service.override(...):`` on every test in
this package. If some future test ALSO overrides ``proximity_service`` and
forgets to clean up, ``_default_proximity_service``'s ``with`` block still runs
its exit on teardown -- but ``reset_last_overriding()`` pops whatever is on TOP
of the override stack, which is now the LEAKED override, not this fixture's own
stub. The stub is left stranded, and unless ``proximity_service`` is covered by
``_rewire_game_modules``'s tripwire (the ``guarded`` tuple), nothing ever
notices: a poisoned container silently reaches later, unrelated tests.

This can only be proven by actually running a test that leaks the override and
watching the *outer* fixture teardown fail -- a unit test calling the fixture
generators directly wouldn't exercise pytest's own fixture teardown ordering,
which is exactly the mechanism at fault. Hence the nested subprocess: a real,
separate pytest invocation, collected under this same directory so the real
``conftest.py`` chain applies to it.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

_LEAK_TEST_BODY = textwrap.dedent("""
    from unittest.mock import MagicMock

    from animetix.containers import container
    from dependency_injector import providers


    def test_leaks_a_proximity_service_override():
        # Deliberately mimics a test that overrides proximity_service and never
        # cleans it up -- no `with` block, no reset_last_overriding(). This is
        # the exact failure mode the tripwire in conftest.py must catch.
        container.core.proximity_service.override(providers.Object(MagicMock()))
    """)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_leak_scratch_file(tmp_name: str) -> subprocess.CompletedProcess:
    scratch = Path(__file__).parent / tmp_name
    scratch.write_text(_LEAK_TEST_BODY, encoding="utf-8")
    try:
        return subprocess.run(
            [sys.executable, "-m", "pytest", str(scratch), "-q"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        scratch.unlink(missing_ok=True)


def test_a_leaked_proximity_service_override_fails_the_test_run():
    result = _run_leak_scratch_file("test_zz_proximity_leak_scratch.py")
    output = result.stdout + result.stderr

    assert result.returncode != 0, (
        "A test that leaks a proximity_service override must fail the run "
        "(the tripwire in conftest.py's _rewire_game_modules must catch it):\n" + output
    )
    assert "leaked container overrides" in output, output
    assert "proximity_service" in output, output
