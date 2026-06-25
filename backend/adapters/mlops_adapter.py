from core.ports.mlops_port import MlopsPort


class MlopsAdapter(MlopsPort):
    def __init__(self):
        from adapters.infrastructure.vertex_pipelines_client import (
            VertexPipelinesClient,
        )

        self.pipelines_client = VertexPipelinesClient()

    def log_dpo_preference(
        self, query: str, chosen: str, rejected: str, project_root: str
    ):
        """
        Appelle la tâche Celery pour journaliser les préférences DPO de manière asynchrone.
        """
        from animetix.tasks_client import enqueue_task  # noqa: E402

        enqueue_task("log_dpo_preference_task", query, chosen, rejected, project_root)

    def trigger_dpo_pipeline(self, min_samples: int = 100) -> dict:
        from pipeline.mlops.vertex_pipelines import dpo_retraining_pipeline

        return self.pipelines_client.submit_pipeline(
            pipeline_func=dpo_retraining_pipeline,
            pipeline_name="dpo-retraining",
            parameter_values={"min_samples": min_samples},
        )

    def trigger_rag_pipeline(self) -> dict:
        from pipeline.mlops.vertex_pipelines import rag_reindexing_pipeline

        return self.pipelines_client.submit_pipeline(
            pipeline_func=rag_reindexing_pipeline,
            pipeline_name="rag-reindexing",
            parameter_values={},
        )

    def list_pipeline_runs(
        self, pipeline_name: "str | None" = None, limit: int = 20
    ) -> list:
        return self.pipelines_client.list_pipeline_runs(pipeline_name, limit)
