from core.ports.mlops_port import MlopsPort


class MlopsAdapter(MlopsPort):
    def log_dpo_preference(self, query: str, chosen: str, rejected: str, project_root: str):
        """
        Appelle la tâche Celery pour journaliser les préférences DPO de manière asynchrone.
        """
        from animetix.tasks import log_dpo_preference_task
        log_dpo_preference_task.delay(query, chosen, rejected, project_root)
