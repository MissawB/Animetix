from unittest.mock import MagicMock

from core.domain.services.self_evolving_compiler import SelfEvolvingCompiler


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
