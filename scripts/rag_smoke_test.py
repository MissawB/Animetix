import json
import os
import sys

# Ajout du dossier root au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_smoke_test():
    """
    Exécute une suite de requêtes RAG et compare les scores.
    """
    print("🧪 Starting RAG Smoke Test...")

    # 1. Charger le baseline
    baseline_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "mlops", "baseline_ragas.json"
    )
    with open(baseline_path, "r") as f:
        baseline = json.load(f)

    # 2. Exécuter l'évaluation actuelle
    from backend.scripts.mlops_rag_eval import run_mlops_eval  # noqa: E402

    current_report = run_mlops_eval()

    # 3. Comparer (exemple simplifié)
    if (
        current_report.get("avg_faithfulness", 0)
        < baseline.get("avg_faithfulness", 0) - 0.05
    ):
        print("🚨 Smoke Test FAILED: Performance regression detected.")
        sys.exit(1)

    print("✅ Smoke Test PASSED: Model performance is stable.")


if __name__ == "__main__":
    run_smoke_test()
