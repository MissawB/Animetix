# -*- coding: utf-8 -*-
"""Provenance des runs d'entraînement MLOps.

Capture de quoi tracer/reproduire un checkpoint : commit git du code, horodatage
UTC, et révisions des modèles de base (depuis le registre central model_registry).
Écrit un `run_metadata.json` à côté du checkpoint — sans dépendance lourde
(ni DVC ni MLflow).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("animetix.mlops.provenance")

# backend/pipeline/mlops/run_provenance.py -> parents[3] = racine du dépôt
REPO_ROOT = Path(__file__).resolve().parents[3]


def get_git_commit() -> str:
    """SHA du commit courant. Priorité à `GIT_COMMIT` (utile en CI/conteneur où le
    `.git` peut être absent), sinon `git rev-parse HEAD`, sinon `"unknown"`."""
    env = os.getenv("GIT_COMMIT")
    if env:
        return env.strip()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return out.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not resolve git commit: {e}")
        return "unknown"


def get_registry_revisions() -> Dict[str, Any]:
    """Révisions des modèles de base (depuis le registre central) pour la traçabilité."""
    try:
        from core.utils.model_registry import EMBEDDING_VERSIONS, get_verified_revision

        revisions: Dict[str, Any] = {}
        for kind, versions in EMBEDDING_VERSIONS.items():
            revisions[kind] = {}
            for version, model_id in versions.items():
                revisions[kind][version] = {
                    "id": model_id,
                    "revision": get_verified_revision(model_id),
                }
        return revisions
    except Exception as e:
        logger.warning(f"Could not read model revisions from registry: {e}")
        return {}


def build_provenance(**extra: Any) -> Dict[str, Any]:
    """Dict de provenance : commit git + timestamp UTC + révisions registre + extras fournis."""
    return {
        "git_commit": get_git_commit(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_models": get_registry_revisions(),
        **extra,
    }


def write_run_metadata(output_dir: os.PathLike | str, **extra: Any) -> Dict[str, Any]:
    """Écrit `run_metadata.json` dans `output_dir` et retourne le dict de provenance."""
    prov = build_provenance(**extra)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote run_metadata.json (commit={prov['git_commit'][:8]}) to {out}")
    return prov
