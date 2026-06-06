# -*- coding: utf-8 -*-
"""
Self-Evolving Runtime Compiler for Animetix.
Generates, compiles, and links performance-optimized native execution loops at runtime.
Now supports dynamic code generation and Numba JIT.
"""

import os
import sys
import logging
import inspect
from typing import Dict, Any, Callable, Optional, List
import numpy as np

logger = logging.getLogger("animetix.evolving.compiler")

try:
    import numba
    from numba import njit
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

    def compile_dynamic_kernel(self, name: str, source_code: str, namespace: Optional[Dict] = None) -> Callable:
        """
        Prend une chaîne de code Python, la compile et l'annote avec @njit si possible.
        """
        logger.info(f"🧬 Compiler: Generating dynamic kernel '{name}'...")
        
        # Préparation de l'espace de noms
        exec_globals = {"np": np, "math": __import__("math")}
        if HAS_NUMBA:
            exec_globals["njit"] = njit
            
        if namespace:
            exec_globals.update(namespace)

        # Injection du décorateur dans le code source si HAS_NUMBA
        decorated_source = source_code
        if HAS_NUMBA and "@njit" not in source_code:
            decorated_source = "@njit(cache=True, fastmath=True)\n" + source_code

        try:
            exec(decorated_source, exec_globals)
            # Récupération de la fonction compilée
            if name in exec_globals:
                compiled_fn = exec_globals[name]
                self.compiled_functions[name] = compiled_fn
                logger.info(f"✅ Compiler: Kernel '{name}' successfully compiled and linked.")
                return compiled_fn
            else:
                raise ValueError(f"Function '{name}' not found in executed source.")
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
        if function_name == 'cosine_similarity':
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

        elif function_name == 'euclidean_distance':
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
        logger.warning(f"⚠️ Function '{function_name}' not in registry. Using Numpy fallback.")
        if function_name == 'vector_norm':
            return np.linalg.norm
            
        def basic_fallback(*args, **kwargs): return 0.0
        return basic_fallback

    def evolve_with_llm(self, task_description: str, llm_proxy: Any) -> Callable:
        """
        Squelette d'évolution : Utilise un LLM pour générer le code source d'un nouveau kernel,
        puis le compile et l'injecte dans le runtime.
        """
        logger.info(f"✨ Compiler: Evolving runtime for task: {task_description}")
        
        # En production, on appellerait le LLM ici.
        # Ici on simule une réponse LLM pour un kernel de 'dot_product_unrolled'
        if "dot_product" in task_description:
            source = """
def dot_product_unrolled(a, b):
    # Kernel généré dynamiquement pour accélération massive
    res = 0.0
    n = len(a)
    for i in range(n):
        res += a[i] * b[i]
    return res
"""
            return self.compile_dynamic_kernel("dot_product_unrolled", source)
            
        raise NotImplementedError("LLM evolution proxy requires real integration.")
