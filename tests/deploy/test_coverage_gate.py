"""Lockstep guard for the backend coverage gate.

Audit dette 2026-07-19: the pre-push hook said `--cov-fail-under=75` while
ci.yml and pyproject.toml said 76 — a push could pass locally at 75.x% and
then fail the CI gate. The three declarations must carry the same number
(pyproject's comment already promises they are "kept in lockstep").
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _gates():
    gates = {}
    for rel in (".pre-commit-config.yaml", ".github/workflows/ci.yml"):
        text = (REPO / rel).read_text(encoding="utf-8")
        for value in re.findall(r"--cov-fail-under=(\d+)", text):
            gates.setdefault(rel, set()).add(int(value))
    toml = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r"^fail_under\s*=\s*(\d+)", toml, re.M)
    assert m, "pyproject.toml no longer declares fail_under — update this guard"
    gates["pyproject.toml"] = {int(m.group(1))}
    return gates


def test_backend_coverage_gate_is_in_lockstep_everywhere():
    gates = _gates()
    assert ".pre-commit-config.yaml" in gates, "pre-push pytest hook lost its gate"
    assert ".github/workflows/ci.yml" in gates, "CI test job lost its gate"
    distinct = set().union(*gates.values())
    assert len(distinct) == 1, f"coverage gates diverge: {gates}"
