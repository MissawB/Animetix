import ast
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]  # project root (scripts/..)
SRC_DIR = BASE_DIR / "src"


def is_missing_type_hints(func: ast.FunctionDef) -> bool:
    # Return True if any argument or return annotation is missing
    for arg in func.args.args:
        if arg.annotation is None:
            return True
    # *args and **kwargs
    if func.args.vararg and func.args.vararg.annotation is None:
        return True
    if func.args.kwarg and func.args.kwarg.annotation is None:
        return True
    # return annotation
    if func.returns is None:
        return True
    return False


def get_function_length(func: ast.FunctionDef) -> int:
    return func.end_lineno - func.lineno + 1 if hasattr(func, "end_lineno") else 0


results = []
for py_file in SRC_DIR.rglob("*.py"):
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                length = get_function_length(node)
                missing_hints = is_missing_type_hints(node)
                if length > 100 or missing_hints:
                    results.append(
                        {
                            "file": str(py_file),
                            "lineno": node.lineno,
                            "name": node.name,
                            "length": length,
                            "missing_type_hints": missing_hints,
                        }
                    )
    except Exception as e:
        print(f"Error processing {py_file}: {e}")

if results:
    print("Potential technical debt findings:")
    for r in results:
        print(
            f"- {r['file']}:{r['lineno']} - {r['name']} (lines: {r['length']}, missing hints: {r['missing_type_hints']})"
        )
else:
    print("No large functions or missing type hints detected.")
