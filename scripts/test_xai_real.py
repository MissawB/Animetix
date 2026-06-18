import os
import sys

# Ajout des chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Setup Django avant d'importer le container
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.animetix_project.settings")
import django  # noqa: E402

try:
    django.setup()
except Exception as e:
    print(f"Erreur de setup Django: {e}")

from api.animetix.containers.agentic import AgenticContainer  # noqa: E402


def main():
    print("🚀 Initialisation du AgenticContainer...")
    container = AgenticContainer()

    # Résolution des dépendances mockées si nécessaire pour le test
    agentic_rag = container.agentic_rag()

    query = "Explique moi le concept de Nen dans Hunter x Hunter."
    print(f"\n🧠 Requête : {query}\n")

    try:
        for step in agentic_rag.plan_and_solve_stream(
            query=query, media_type="anime", user_id="test_user"
        ):
            step_type = step.get("type")
            if step_type == "xai_report":
                print("\n\n" + "=" * 60)
                print("📊 RAPPORT XAI (EXPLAINABLE AI) GÉNÉRÉ :")
                print("=" * 60)
                import json  # noqa: E402

                print(json.dumps(step.get("content"), indent=2, ensure_ascii=False))
                print("=" * 60 + "\n")
            elif step_type == "thought":
                print(f"💭 {step.get('content')}")
            elif step_type == "token":
                print(step.get("content"), end="", flush=True)
            elif step_type == "eval":
                pass  # skip eval output to keep console clean
    except Exception as e:
        print(f"\n❌ Erreur pendant le stream: {e}")


if __name__ == "__main__":
    main()
