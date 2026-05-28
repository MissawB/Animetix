# -*- coding: utf-8 -*-
import time
import numpy as np
import sys
import os

# Ajout du path src
sys.path.append(os.path.abspath("src"))

from core.domain.services.self_evolving_compiler import SelfEvolvingCompiler

def benchmark_performance():
    print("🚀 Starting SelfEvolvingCompiler Benchmark (Numba JIT vs Python/Numpy)...")
    compiler = SelfEvolvingCompiler()
    
    # Génération de données de test (vecteurs larges pour voir la différence)
    N = 1000000
    a = np.random.rand(N).astype(np.float64)
    b = np.random.rand(N).astype(np.float64)
    
    print(f"📊 Vector size: {N}")
    print(f"🔧 Compiler Mode: {compiler.mode}")

    # 1. Benchmark Cosine Similarity
    print("\n--- Cosine Similarity ---")
    
    # Version Python pure (très lente sur 1M d'éléments)
    def python_cosine(a, b):
        dot = sum(x*y for x,y in zip(a,b))
        norm_a = sum(x*x for x in a)**0.5
        norm_b = sum(x*x for x in b)**0.5
        return dot / (norm_a * norm_b)
    
    # Version Numpy
    start = time.perf_counter()
    res_np = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    end = time.perf_counter()
    print(f"🕒 Numpy: {(end-start)*1000:.4f} ms")

    # Version Compiler (Numba)
    opt_cosine = compiler.analyze_and_optimize('cosine_similarity')
    
    # Warmup (First call compiles)
    opt_cosine(a, b)
    
    start = time.perf_counter()
    res_opt = opt_cosine(a, b)
    end = time.perf_counter()
    print(f"🕒 {compiler.mode}: {(end-start)*1000:.4f} ms")
    
    print(f"✅ Results match: {np.isclose(res_np, res_opt)}")

    # 2. Benchmark Euclidean Distance
    print("\n--- Euclidean Distance ---")
    
    start = time.perf_counter()
    res_np_dist = np.linalg.norm(a - b)
    end = time.perf_counter()
    print(f"🕒 Numpy: {(end-start)*1000:.4f} ms")

    opt_euclidean = compiler.analyze_and_optimize('euclidean_distance')
    opt_euclidean(a, b) # Warmup
    
    start = time.perf_counter()
    res_opt_dist = opt_euclidean(a, b)
    end = time.perf_counter()
    print(f"🕒 {compiler.mode}: {(end-start)*1000:.4f} ms")

    print(f"✅ Results match: {np.isclose(res_np_dist, res_opt_dist)}")

if __name__ == "__main__":
    benchmark_performance()
