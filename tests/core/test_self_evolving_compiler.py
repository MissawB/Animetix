from unittest.mock import MagicMock

import pytest
from core.domain.services.self_evolving_compiler import (
    _SAFE_BUILTINS,
    SelfEvolvingCompiler,
    UnsafeKernelError,
    assert_safe_kernel_source,
)


def test_compiler_initialization():
    compiler = SelfEvolvingCompiler(build_dir="tests/test_build")
    assert compiler.build_dir == "tests/test_build"
    assert isinstance(compiler.compiled_functions, dict)
    assert len(compiler.compiled_functions) == 0


def test_compile_dynamic_kernel():
    compiler = SelfEvolvingCompiler(build_dir="tests/test_build")
    source_code = """
def add(a, b):
    return a + b
"""
    func = compiler.compile_dynamic_kernel("add", source_code)
    assert callable(func)
    assert func(1, 2) == 3
    assert "add" in compiler.compiled_functions


def test_analyze_and_optimize():
    compiler = SelfEvolvingCompiler(build_dir="tests/test_build")
    # Test known function
    func = compiler.analyze_and_optimize("cosine_similarity")
    assert callable(func)
    assert "cosine_similarity" in compiler.compiled_functions

    # Test unknown function fallback
    fallback_func = compiler.analyze_and_optimize("unknown_func")
    assert callable(fallback_func)
    assert fallback_func() == 0.0


def test_evolve_with_llm_fallback():
    compiler = SelfEvolvingCompiler(build_dir="tests/test_build")
    mock_llm = MagicMock()
    mock_llm.generate.side_effect = Exception("LLM failure")

    func = compiler.evolve_with_llm("do nothing", mock_llm)
    assert callable(func)
    assert func() == 0.0


# --- RCE guard (security) -------------------------------------------------


def test_safe_kernel_source_allows_numeric_kernel():
    # A legitimate pure-numeric kernel must pass the gate unchanged.
    assert_safe_kernel_source(
        "def k(a, b):\n"
        "    s = 0.0\n"
        "    for i in range(len(a)):\n"
        "        s += a[i] * b[i]\n"
        "    return np.sqrt(s)\n"
    )


@pytest.mark.parametrize(
    "malicious",
    [
        "import os\ndef k():\n    return os.system('id')",
        "from subprocess import run\ndef k():\n    run(['id'])",
        "def k():\n    return __import__('os').system('id')",
        "def k():\n    return eval('1+1')",
        "def k():\n    return open('/etc/passwd').read()",
        "def k():\n    return ().__class__.__bases__[0].__subclasses__()",
        "def k():\n    return subprocess.run(['id'])",
        "def k():\n    return globals()",
    ],
)
def test_safe_kernel_source_rejects_malicious(malicious):
    with pytest.raises(UnsafeKernelError):
        assert_safe_kernel_source(malicious)


def test_safe_kernel_source_rejects_syntax_error():
    with pytest.raises(UnsafeKernelError):
        assert_safe_kernel_source("def k(:\n  pass")


def test_compile_dynamic_kernel_rejects_malicious_source():
    compiler = SelfEvolvingCompiler(build_dir="tests/test_build")
    with pytest.raises(UnsafeKernelError):
        compiler.compile_dynamic_kernel(
            "evil", "import os\ndef evil():\n    os.system('id')"
        )
    assert "evil" not in compiler.compiled_functions


def test_evolve_with_llm_rejects_injected_code_and_falls_back():
    # A prompt-injected LLM response carrying an import must NOT be executed; the
    # compiler swallows the UnsafeKernelError and returns the null fallback.
    compiler = SelfEvolvingCompiler(build_dir="tests/test_build")
    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        "```python\nimport os\ndef pwn():\n    os.system('rm -rf /')\n```"
    )

    func = compiler.evolve_with_llm("optimize", mock_llm)
    assert callable(func)
    assert func() == 0.0  # the null error_fallback, not the injected code
    assert "pwn" not in compiler.compiled_functions


def test_exec_namespace_withholds_dangerous_builtins():
    # Defense-in-depth: the exec sandbox builtins must exclude import/open/eval/exec.
    for forbidden in ("__import__", "open", "eval", "exec", "compile", "getattr"):
        assert forbidden not in _SAFE_BUILTINS
    # ...while keeping what numeric kernels need.
    for needed in ("range", "len", "abs", "float"):
        assert needed in _SAFE_BUILTINS
