from core.ports.mlops_port import MlopsPort


class MlopsAdapter(MlopsPort):
    def log_dpo_preference(self, query: str, chosen: str, rejected: str, project_root: str):
        """
        Appelle la tâche Celery pour journaliser les préférences DPO de manière asynchrone.
        """
        from animetix.tasks_client import enqueue_task
        enqueue_task("log_dpo_preference_task", query, chosen, rejected, project_root)
