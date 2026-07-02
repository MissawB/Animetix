import os
import sys

import django

# Set up python path correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend"))
sys.path.insert(0, os.path.join(project_root, "backend", "api"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
django.setup()

from animetix.containers import container  # noqa: E402


def main():
    print("Initializing MLOps adapter...")
    mlops_port = container.agentic.mlops_adapter_factory()

    # Triggering the STaR LoRA fine-tuning pipeline
    print("Submitting STaR LoRA Fine-Tuning pipeline to Vertex AI...")
    try:
        result = mlops_port.trigger_star_pipeline()
        print("Success! Pipeline run details:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error submitting STaR pipeline: {e}")


if __name__ == "__main__":
    main()
