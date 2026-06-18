import os
import sys
import django
import json
from tqdm import tqdm

# Setup environment
# Assuming script is in scripts/curate_dpo_dataset.py
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
django.setup()

from animetix.models import AIFeedback  # noqa: E402
from animetix.containers import get_container  # noqa: E402
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop  # noqa: E402


def curate_dpo_dataset():
    print("🚀 Starting Swarm-to-DPO Curation...")
    container = get_container()
    rag = container.agentic_rag()
    loop = DPOFeedbackLoop(prompt_manager=container.prompt_manager())

    # 1. Fetch rejected feedbacks
    rejected = AIFeedback.objects.filter(is_positive=False)
    print(f"📊 Found {len(rejected)} negative feedback entries.")

    if not rejected.exists():
        print("ℹ️ No negative feedback to curate. Exiting.")
        return

    output_path = os.path.join(
        base_dir, "data", "mlops", "datasets", "dpo_train_swarm.jsonl"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    processed_count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for fb in tqdm(rejected, desc="Curation with Swarm"):
            # Generate perfect answer with Swarm
            try:
                # Use standard solve which uses Swarm/Thinking mode automatically
                # Defaulting media_type to "Anime" if not present in feedback
                media_type = getattr(fb, "media_type", "Anime")
                chosen = rag.plan_and_solve(fb.input_context, media_type)

                entry = {
                    "context": fb.input_context,
                    "output": fb.output_text,  # The rejected one
                    "is_positive": False,
                }

                if loop.validate_feedback(entry):
                    pair = loop.create_dpo_pair(entry, chosen_override=chosen)
                    f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                    processed_count += 1
            except Exception as e:
                print(f"   ⚠️ Failed to curate feedback {fb.id}: {e}")

    print(f"✨ Curation complete: {processed_count} DPO pairs saved to {output_path}")


if __name__ == "__main__":
    curate_dpo_dataset()
