"""Supply-chain guard for GitHub Actions references.

Audit dette 2026-07-19: `jlumbroso/free-disk-space@main` appeared in 6 jobs —
a mutable branch ref lets an upstream push silently change what runs in CI.
Actions must be pinned to a tag or a commit SHA; branch refs are forbidden.
"""

import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"

MUTABLE_BRANCH_REFS = ("main", "master", "dev", "develop", "trunk")


def test_no_action_is_pinned_to_a_mutable_branch():
    offenders = []
    for wf in sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml")):
        for lineno, line in enumerate(
            wf.read_text(encoding="utf-8").splitlines(), start=1
        ):
            m = re.search(r"uses:\s*([\w./-]+)@([\w.-]+)", line)
            if m and m.group(2) in MUTABLE_BRANCH_REFS:
                offenders.append(f"{wf.name}:{lineno} -> {m.group(0).strip()}")
    assert (
        not offenders
    ), f"actions pinned to a mutable branch (use a tag or commit SHA): {offenders}"
