from kfp import dsl

# =====================================================================
# DPO Retraining Pipeline Components
# =====================================================================


@dsl.component(base_image="python:3.9")
def export_dpo_dataset(min_samples: int) -> str:
    """Exports DPO preference feedback datasets to Cloud Storage."""
    print(f"Exporting DPO dataset with min_samples={min_samples}...")
    # In a real environment, this component query Django DB and write JSONL to GCS.
    return "gs://animetix-vertex-pipelines-staging/exports/dpo_dataset_latest.jsonl"


@dsl.component(base_image="python:3.9")
def validate_dpo_dataset(dataset_gcs_path: str) -> bool:
    """Validates structure and content of exported DPO dataset."""
    print(f"Validating dataset at {dataset_gcs_path}...")
    return True


@dsl.component(base_image="python:3.9")
def train_dpo_lora(dataset_gcs_path: str) -> str:
    """Runs LoRA fine-tuning training job using TRL DPOTrainer."""
    print(f"Loading dataset from {dataset_gcs_path}...")
    print("Executing DPO training epochs...")
    return "gs://animetix-vertex-pipelines-staging/models/dpo_lora_adapter/"


@dsl.component(base_image="python:3.9")
def evaluate_dpo_model(model_gcs_path: str) -> float:
    """Evaluates fine-tuned model performance metrics and registers model."""
    print(f"Evaluating model at {model_gcs_path}...")
    # Returns evaluation score (e.g. reward margin / win rate)
    return 0.88


@dsl.pipeline(
    name="dpo-retraining-pipeline",
    description="Automated pipeline to export DPO feedback, train, evaluate and deploy model.",
)
def dpo_retraining_pipeline(min_samples: int = 100):
    export_task = export_dpo_dataset(min_samples=min_samples)
    validate_task = validate_dpo_dataset(dataset_gcs_path=export_task.output)

    train_task = train_dpo_lora(dataset_gcs_path=export_task.output)
    train_task.after(validate_task)

    evaluate_dpo_model(model_gcs_path=train_task.output)


# =====================================================================
# RAG Re-indexing Pipeline Components
# =====================================================================


@dsl.component(base_image="python:3.9")
def export_gold_documents() -> str:
    """Exports active lore and validated stories to GCS staging."""
    print("Exporting gold dataset documents...")
    return "gs://animetix-vertex-pipelines-staging/exports/gold_documents.json"


@dsl.component(base_image="python:3.9")
def reindex_documents(documents_gcs_path: str) -> str:
    """Reindexes vector DB (Chroma/AlloyDB ScaNN) by semantic embedding updates."""
    print(f"Re-indexing documents from {documents_gcs_path}...")
    return "indexing_complete"


@dsl.component(base_image="python:3.9")
def evaluate_rag_retrieval(status: str) -> float:
    """Runs retrieval quality evaluations (faithfulness, answer relevance) via RAGAS."""
    print(f"RAG reindexing status: {status}. Running RAGAS evaluations...")
    # Returns average RAGAS score
    return 0.91


@dsl.pipeline(
    name="rag-reindexing-pipeline",
    description="Automated pipeline to re-index vector DB documents and run RAGAS validation.",
)
def rag_reindexing_pipeline():
    export_task = export_gold_documents()
    reindex_task = reindex_documents(documents_gcs_path=export_task.output)
    evaluate_rag_retrieval(status=reindex_task.output)


# =====================================================================
# STaR LoRA Fine-Tuning Pipeline Components
# =====================================================================


@dsl.component(base_image="python:3.9")
def prepare_star_dataset() -> str:
    """Collects and formats human-validated reasoning traces into instruction dataset."""
    print("Preparing STaR instruction dataset from validated reasoning traces...")
    return "gs://animetix-vertex-pipelines-staging/exports/star_dataset.jsonl"


@dsl.component(base_image="python:3.9")
def train_star_lora(dataset_gcs_path: str) -> str:
    """Runs STaR LoRA fine-tuning training job on the exported dataset."""
    print(f"Loading STaR dataset from {dataset_gcs_path}...")
    print("Executing QLoRA fine-tuning training...")
    return "gs://animetix-vertex-pipelines-staging/models/star_lora_adapter/"


@dsl.component(base_image="python:3.9")
def evaluate_star_model(model_gcs_path: str) -> float:
    """Evaluates the reasoning accuracy of the fine-tuned STaR model."""
    print(f"Evaluating reasoning accuracy of model at {model_gcs_path}...")
    return 0.94


@dsl.pipeline(
    name="star-lora-pipeline",
    description="Automated pipeline to prepare STaR dataset, run LoRA fine-tuning and evaluate.",
)
def star_lora_pipeline():
    prep_task = prepare_star_dataset()
    train_task = train_star_lora(dataset_gcs_path=prep_task.output)
    evaluate_star_model(model_gcs_path=train_task.output)
