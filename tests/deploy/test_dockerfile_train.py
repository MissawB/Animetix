"""Reproducibility guards for deploy/Dockerfile.train.

Audit dette 2026-07-19: the training image floated (`trl>=0.12.0`,
`transformers>=4.57.0`, base tag without digest) while the serving lock pins
exact versions — so a LoRA could be trained on library versions never tested
in prod, and a rebuild months later would silently produce a different env.

Invariants:
1. the base image is pinned by digest;
2. every pip spec in the Dockerfile is `==`-pinned;
3. the packages shared with the service lock match requirements.txt exactly
   (train env stays in lockstep with the serve env — bump them together).
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO / "deploy" / "Dockerfile.train"
LOCK = REPO / "requirements.txt"

# Packages installed by the Dockerfile that also exist in the serving lock.
LOCKSTEP_PACKAGES = [
    "trl",
    "peft",
    "transformers",
    "accelerate",
    "datasets",
    "bitsandbytes",
]


@pytest.fixture(scope="module")
def dockerfile():
    return DOCKERFILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pip_specs(dockerfile):
    """Every quoted requirement spec inside the `pip install` RUN layer."""
    run_block = re.search(r"RUN pip install.*?(?:\n\n|\Z)", dockerfile, re.S)
    assert run_block, "no `RUN pip install` layer found in Dockerfile.train"
    specs = re.findall(r'"([^"]+)"', run_block.group(0))
    assert specs, "no pip specs found in Dockerfile.train — parsing broke?"
    return specs


@pytest.fixture(scope="module")
def lock_versions():
    versions = {}
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;#]+)", line.strip())
        if m:
            versions[m.group(1).lower().replace("_", "-")] = m.group(2)
    return versions


def test_base_image_is_pinned_by_digest(dockerfile):
    from_line = next(
        line for line in dockerfile.splitlines() if line.startswith("FROM ")
    )
    assert "@sha256:" in from_line, (
        "Dockerfile.train FROM must pin the base image by digest "
        f"(mutable tag found: {from_line!r})"
    )


def test_every_pip_spec_is_exact_pinned(pip_specs):
    floating = [s for s in pip_specs if "==" not in s]
    assert not floating, f"floating pip specs in Dockerfile.train: {floating}"


def test_lockstep_packages_match_the_serving_lock(pip_specs, lock_versions):
    pinned = {}
    for spec in pip_specs:
        if "==" in spec:
            name, version = spec.split("==", 1)
            pinned[name.lower().replace("_", "-")] = version

    mismatches = {
        pkg: (pinned.get(pkg), lock_versions.get(pkg))
        for pkg in LOCKSTEP_PACKAGES
        if pinned.get(pkg) != lock_versions.get(pkg)
    }
    assert not mismatches, (
        "Dockerfile.train diverges from requirements.txt "
        f"(dockerfile, lock): {mismatches}"
    )
