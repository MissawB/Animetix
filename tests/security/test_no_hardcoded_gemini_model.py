import ast
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
ALLOWED = BACKEND / "core" / "utils" / "gemini_models.py"
PATTERN = re.compile(r"gemini-[\w.-]*\d")


def _docstring_ids(tree: ast.AST) -> set:
    """`id()` des constantes-chaînes qui sont des docstrings (1er statement d'un
    module / classe / fonction). Une mention d'un modèle dans une docstring (ex.
    exemple de format de log) est de la prose, pas un choix de modèle hardcodé."""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = getattr(node, "body", None)
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def test_no_hardcoded_gemini_model_literal():
    """Interdit les littéraux de modèle Gemini codés en dur dans le CODE (chaînes
    utilisées comme valeurs) — le choix de modèle doit passer par une constante de
    rôle de `core.utils.gemini_models`. Les commentaires (`#`, absents de l'AST) et
    les docstrings sont ignorés : y mentionner un modèle en exemple est légitime."""
    offenders = []
    for py in BACKEND.rglob("*.py"):
        if py.resolve() == ALLOWED.resolve():
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        docstrings = _docstring_ids(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
                and PATTERN.search(node.value)
            ):
                offenders.append(
                    f"{py}:{getattr(node, 'lineno', '?')}: {node.value.strip()[:80]}"
                )
    assert not offenders, (
        "Hardcoded Gemini/embedding model literal found in code; import a role "
        "constant from core.utils.gemini_models instead.\n" + "\n".join(offenders)
    )
