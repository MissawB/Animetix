import argparse
import json

from animetix.containers import get_container
from core.domain.services.long_context_service import LongContextDiscoveryService


def run_evaluation(max_size=32000):
    """
    Script d'évaluation de la mémoire longue (Needle In A Haystack).
    """
    print("🚀 Starting Long-Context Memory Evaluation (Animetix RULER-lite)...")

    container = get_container()
    long_ctx_service = LongContextDiscoveryService(
        inference_engine=container.inference_engine()
    )

    sizes = [2000, 8000, 16000, 32000]
    # Filtrer les tailles qui dépassent la limite du modèle actuel
    sizes = [s for s in sizes if s <= max_size]

    results = long_ctx_service.benchmark_model_limits(sizes=sizes)

    # Calcul des stats
    total = len(results)
    successes = sum(1 for r in results if r["success"])
    avg_latency = sum(r["latency_sec"] for r in results) / total

    print("\n" + "=" * 40)
    print(f"📊 FINAL RESULTS (Max Context: {max_size})")
    print(f"✅ Accuracy: {(successes / total) * 100:.2f}% ({successes}/{total})")
    print(f"⏱️  Avg Latency: {avg_latency:.2f}s")
    print("=" * 40)

    # Save to data/mlops
    output_path = "data/mlops/long_context_benchmark.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"💾 Report saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-size", type=int, default=32000)
    args = parser.parse_args()

    run_evaluation(max_size=args.max_size)
