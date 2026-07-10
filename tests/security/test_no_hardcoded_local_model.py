"""Anti-literal guard for LOCAL model ids (Phase 2b of the model registry).

Mirrors ``test_no_hardcoded_gemini_model.py``: every local/self-hosted model id
(Ollama tags, Qwen/FLUX/VibeThinker Hub repos) must come from the logical-role
constants in ``core/utils/local_models.py`` — hardcoded literals drift (the
audit found ``llama3`` vs ``qwen3.5`` and ``Qwen2.5-1.5B`` vs ``Qwen3.5-4B``
defaults disagreeing across adapters).

Allowlisted files are registries/catalogs whose PURPOSE is to enumerate model
ids (SHA-pinning registry, pricing table, SOTA benchmark catalog).
"""

import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
ALLOWED = {
    (BACKEND / "core" / "utils" / "local_models.py").resolve(),
    (BACKEND / "core" / "utils" / "model_registry.py").resolve(),
    (BACKEND / "core" / "domain" / "services" / "pricing_service.py").resolve(),
    (BACKEND / "core" / "domain" / "services" / "sota_benchmark_service.py").resolve(),
}
# Quoted string literals only (comments/prose stay free to mention model names).
PATTERN = re.compile(r"""["'](?:Qwen/|WeiboAI/|black-forest-labs/|qwen3\.5|llama3\b)""")


def test_no_hardcoded_local_model_literal():
    offenders = []
    for py in BACKEND.rglob("*.py"):
        if py.resolve() in ALLOWED or "__pycache__" in py.parts:
            continue
        for i, line in enumerate(
            py.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            if PATTERN.search(line):
                offenders.append(f"{py.relative_to(BACKEND)}:{i}: {line.strip()}")
    assert not offenders, (
        "Hardcoded local model literal found; import a role constant from "
        "core.utils.local_models instead.\n" + "\n".join(offenders)
    )
