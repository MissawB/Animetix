import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
ALLOWED = BACKEND / "core" / "utils" / "gemini_models.py"
PATTERN = re.compile(r"gemini-[\w.-]*\d")


def test_no_hardcoded_gemini_model_literal():
    offenders = []
    for py in BACKEND.rglob("*.py"):
        if py.resolve() == ALLOWED.resolve():
            continue
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if PATTERN.search(line):
                offenders.append(f"{py}:{i}: {line.strip()}")
    assert not offenders, (
        "Hardcoded Gemini/embedding model literal found; import a role constant "
        "from core.utils.gemini_models instead.\n" + "\n".join(offenders)
    )
