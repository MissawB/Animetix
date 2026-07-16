import os
import sys

# Set up paths relative to workspace root with insert(0) to bypass name conflicts
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
api_path = os.path.join(backend_path, "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

# Re-export the module-level names the compiler bridges through sys.modules
# (see core.dpo_feedback_loop.fetch_db_feedbacks) and that tests patch here.
from core.domain.services.dpo_feedback_loop import (  # noqa: E402,F401
    AIFeedback,
    DPOFeedbackLoop,
    django_available,
)

if __name__ == "__main__":
    loop = DPOFeedbackLoop(data_dir="data/mlops/datasets")
    loop.process_and_export(
        raw_data_path="data/mlops/datasets/ai_feedback.jsonl",
        output_path="data/mlops/datasets/dpo_train_v2.jsonl",
    )
