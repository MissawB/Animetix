# -*- coding: utf-8 -*-
"""
Self-Evolving Runtime Compiler for Animetix.
Generates, compiles, and links performance-optimized native execution loops at runtime.
Now supports dynamic code generation and Numba JIT.
"""

import ast  # noqa: E402
import builtins  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable, Dict, Optional  # noqa: E402

import numpy as np  # noqa: E402

logger = logging.getLogger("animetix.evolving.compiler")


class UnsafeKernelError(ValueError):
    """Raised when dynamic kernel source fails the security validation gate."""


# Builtins a numeric kernel legitimately needs. Everything else (eval / exec /
# open / __import__ / getattr / ...) is deliberately withheld so that code passed
# to ``exec`` cannot reach the host even if the AST gate is ever bypassed.
_SAFE_BUILTIN_NAMES = frozenset(
    {
        "abs",
        "min",
        "max",
        "sum",
        "len",
        "range",
        "enumerate",
        "zip",
        "round",
        "pow",
        "int",
        "float",
        "bool",
        "complex",
    }
)
_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in _SAFE_BUILTIN_NAMES
    if hasattr(builtins, name)
}

# Names that must never appear in a dynamic kernel. This is belt-and-suspenders on
# top of the restricted builtins + AST gate (imports + dunder access are blocked
# structurally below).
_FORBIDDEN_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "input",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
        "exit",
        "quit",
        "help",
        "dir",
        "memoryview",
        "bytearray",
        "os",
        "sys",
        "subprocess",
        "importlib",
        "socket",
        "shutil",
        "pathlib",
        "builtins",
        "ctypes",
        "pickle",
        "marshal",
    }
)


def assert_safe_kernel_source(source: str) -> None:
    """Validate LLM/dynamic kernel source before ``exec`` (RCE guard).

    Rejects anything outside a pure numeric kernel: imports, dunder attribute
    access (blocks ``().__class__.__subclasses__()`` style escapes), and a blocklist
    of dangerous names. Raises :class:`UnsafeKernelError` on violation.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise UnsafeKernelError(f"Kernel source is not valid Python: {e}") from e

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise UnsafeKernelError("imports are not allowed in dynamic kernels")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise UnsafeKernelError(
                f"dunder attribute access is not allowed: {node.attr!r}"
            )
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise UnsafeKernelError(f"use of forbidden name: {node.id!r}")


try:
    import numba  # noqa: E402, F401
    from numba import njit  # noqa: E402

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    logger.warning("Numba not found. SelfEvolvingCompiler will use Numpy fallback.")


class SelfEvolvingCompiler:
    def __init__(self, build_dir: str = "data/mlops/build"):
        self.build_dir = build_dir
        os.makedirs(build_dir, exist_ok=True)
        self.compiled_functions: Dict[str, Callable] = {}
        self.mode = "Numba JIT" if HAS_NUMBA else "Numpy Fallback"
        logger.info(f"Initialized SelfEvolvingCompiler in {self.mode} mode.")

    def compile_dynamic_kernel(
        self, name: str, source_code: str, namespace: Optional[Dict] = None
    ) -> Callable:
        """
        Prend une chaîne de code Python, la compile et l'annote avec @njit si possible.
        """
        logger.info(f"🧬 Compiler: Generating dynamic kernel '{name}'...")

        # Nettoyage du code source
        source_code = source_code.strip()

        # --- RCE GUARD ---
        # Kernel source can originate from an LLM (evolve_with_llm); a prompt
        # injection could otherwise smuggle arbitrary code into exec(). Validate the
        # AST before doing anything with it.
        assert_safe_kernel_source(source_code)

        # Préparation de l'espace de noms. ``__builtins__`` is restricted to a safe
        # numeric subset so exec'd code has no access to import/open/eval/etc.
        exec_globals: Dict[str, Any] = {
            "__builtins__": _SAFE_BUILTINS,
            "np": np,
            "math": __import__("math"),
        }
        if HAS_NUMBA:
            exec_globals["njit"] = njit

        if namespace:
            exec_globals.update(namespace)

        # Injection du décorateur dans le code source si HAS_NUMBA
        decorated_source = source_code
        if HAS_NUMBA and "@njit" not in source_code:
            # Note: On désactive cache=True pour les kernels dynamiques via exec() car Numba
            # ne peut pas mettre en cache des fonctions sans fichier source réel sur le disque.
            decorated_source = "@njit(cache=False, fastmath=True)\n" + source_code

        try:
            # nosec B102 - source is AST-validated (assert_safe_kernel_source) and
            # exec runs with restricted __builtins__ (_SAFE_BUILTINS); no imports,
            # dunder access or dangerous names can reach this point.
            exec(decorated_source, exec_globals)  # nosec B102
            # Récupération de la fonction compilée
            if name in exec_globals:
                compiled_fn = exec_globals[name]
                self.compiled_functions[name] = compiled_fn
                logger.info(
                    f"✅ Compiler: Kernel '{name}' successfully compiled and linked."
                )
                return compiled_fn
            else:
                # Tentative de trouver la première fonction définie si le nom ne correspond pas exactement
                for key, val in exec_globals.items():
                    if callable(val) and key != "njit" and not key.startswith("__"):
                        logger.warning(
                            f"⚠️ Compiler: Requested '{name}' not found, but found '{key}'. Linking '{key}' instead."
                        )
                        self.compiled_functions[key] = val
                        return val
                raise ValueError(
                    f"No callable found in executed source for kernel '{name}'."
                )
        except Exception as e:
            logger.error(f"❌ Compiler: Dynamic compilation failed for '{name}': {e}")
            raise

    def analyze_and_optimize(self, function_name: str) -> Callable:
        """
        Fournit une implémentation optimisée.
        """
        if function_name in self.compiled_functions:
            return self.compiled_functions[function_name]

        # Implémentations statiques existantes converties en dynamic kernels
        if function_name == "cosine_similarity":
            source = """
def cosine_similarity(a, b):
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for i in range(len(a)):
        dot += a[i] * b[i]
        norm_a += a[i] * a[i]
        norm_b += b[i] * b[i]
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (np.sqrt(norm_a) * np.sqrt(norm_b))
"""
            return self.compile_dynamic_kernel(function_name, source)

        elif function_name == "euclidean_distance":
            source = """
def euclidean_distance(a, b):
    dist = 0.0
    for i in range(len(a)):
        diff = a[i] - b[i]
        dist += diff * diff
    return np.sqrt(dist)
"""
            return self.compile_dynamic_kernel(function_name, source)

        # Fallback Numpy direct si non reconnu pour compilation custom
        logger.warning(
            f"⚠️ Function '{function_name}' not in registry. Using Numpy fallback."
        )
        if function_name == "vector_norm":
            return np.linalg.norm

        def basic_fallback(*args, **kwargs):
            return 0.0

        return basic_fallback

    def evolve_with_llm(self, task_description: str, llm_proxy: Any) -> Callable:
        """
        Génère dynamiquement un kernel de calcul optimisé via LLM, puis le compile.
        """
        logger.info(f"✨ Compiler: Evolving runtime for task: {task_description}")

        system_prompt = (
            "Tu es un expert en calcul scientifique et optimisation Numba. "
            "Génère une fonction Python pure optimisée pour Numba @njit. "
            "Règles strictes :\n"
            "1. Utilise uniquement 'np' (Numpy) et 'math'.\n"
            "2. Pas de types Python complexes (dict, list comprehensions complexes).\n"
            "3. Utilise des boucles explicites pour une performance maximale.\n"
            "4. Retourne UNIQUEMENT le bloc de code Python dans une balise ```python.\n"
            "5. Ne mets pas le décorateur @njit, le compilateur l'ajoutera.\n"
            "6. Donne à la fonction un nom descriptif en snake_case."
        )

        user_prompt = f"Génère un kernel de calcul Python pour la tâche suivante : {task_description}"

        try:
            # Appel au LLM
            raw_response = llm_proxy.generate(
                prompt=user_prompt, system_prompt=system_prompt
            )

            # Extraction du bloc de code
            code_match = re.search(r"```python\n(.*?)```", raw_response, re.DOTALL)
            if not code_match:
                # Fallback si pas de balises
                code_match = re.search(r"def .*?\):.*", raw_response, re.DOTALL)
                if not code_match:
                    raise ValueError("Could not extract Python code from LLM response.")

            source_code = (
                code_match.group(1)
                if "```python" in raw_response
                else code_match.group(0)
            )

            # Détection du nom de la fonction
            name_match = re.search(r"def\s+([a-zA-Z0-9_]+)\s*\(", source_code)
            function_name = name_match.group(1) if name_match else "dynamic_kernel"

            # Compilation
            return self.compile_dynamic_kernel(function_name, source_code)

        except Exception as e:
            logger.error(f"❌ Compiler Evolution failed: {e}")

            # Fallback vers une fonction nulle pour éviter de casser le pipeline
            def error_fallback(*args, **kwargs):
                return 0.0

            return error_fallback
