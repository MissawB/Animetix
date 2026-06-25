import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
ALLOWED = BACKEND / "core" / "utils" / "local_models.py"
PATTERN = re.compile(
    r"os\.getenv\(\s*[\"'](?:LLM_MODEL_NAME|LOCAL_MODEL_ID|DRAFT_MODEL_ID"
    r"|COMPACT_MODEL_ID|LOCAL_DIFFUSION_MODEL)[\"']"
)


def test_local_model_env_reads_only_in_registry():
    offenders = []
    for py in BACKEND.rglob("*.py"):
        if py.resolve() == ALLOWED.resolve():
            continue
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if PATTERN.search(line):
                offenders.append(f"{py}:{i}: {line.strip()}")
    assert not offenders, (
        "Local-model env reads must live only in core.utils.local_models; "
        "import the role constant instead.\n" + "\n".join(offenders)
    )
