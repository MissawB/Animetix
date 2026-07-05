"""Tripwire du namespace unique (racine nue).

Historique: le même package était importable sous 2-3 identités
(animetix vs backend.api.animetix, core vs backend.core, plus l'alias legacy
src.pipeline), au point que middleware.py synchronisait ses contextvars entre
les copies. Ces tests verrouillent la racine nue.
Voir docs/plans/2026-07-05-unify-import-namespace-design.md.
"""

import importlib
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ("backend", "tests", "scripts")
FORBIDDEN = re.compile(
    r"(?:from\s+backend\.|import\s+backend\.|src\.pipeline"
    r"|[\"']backend\.(?:api|core|adapters|pipeline|animetix|scripts))"
)


def _offending_lines():
    hits = []
    for top in SCAN_DIRS:
        for path in (REPO / top).rglob("*.py"):
            if "__pycache__" in path.parts or path == pathlib.Path(__file__):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if FORBIDDEN.search(line):
                    hits.append(f"{path.relative_to(REPO)}:{lineno}: {line.strip()}")
    return hits


def test_no_backend_or_src_namespace_references():
    hits = _offending_lines()
    assert (
        not hits
    ), "Références au namespace interdit (backend.*/src.pipeline) :\n" + "\n".join(hits)


def test_importing_backend_namespace_raises():
    # Le garde backend/__init__.py doit lever, même pour les chaînes dynamiques
    # (import_string de Django) — c'est la couche runtime du tripwire.
    with pytest.raises(ImportError, match="racine nue"):
        importlib.import_module("backend")
