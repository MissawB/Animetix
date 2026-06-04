import os
import json
import logging
from google.cloud.workflows.executions_v1 import ExecutionsClient
from google.cloud.workflows.executions_v1.types import Execution

logger = logging.getLogger("animetix.workflows")

class GCPWorkflowsClient:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "animetix-prod")
        self.location = os.getenv("GCP_LOCATION", "europe-west1")
        self.workflow_id = os.getenv("GCP_WORKFLOW_ID", "manga-voice-pipeline")
        
        self.client = ExecutionsClient()
        self.parent = f"projects/{self.project_id}/locations/{self.location}/workflows/{self.workflow_id}"

    def trigger_pipeline(self, image_b64: str, reference_audio_b64: str, target_lang: str, filename: str) -> str:
        arguments = {
            "brain_url": os.getenv("BRAIN_API_URL", "http://localhost:7861"),
            "api_key": os.getenv("BRAIN_API_KEY", "dev-insecure-key-animetix-2026"),
            "image": image_b64,
            "reference_audio": reference_audio_b64,
            "target_lang": target_lang,
            "gcs_bucket": os.getenv("GCS_MEDIA_BUCKET", "animetix-media-bucket"),
            "filename": filename
        }

        execution = Execution(argument=json.dumps(arguments))
        response = self.client.create_execution(parent=self.parent, execution=execution)
        logger.info(f"Triggered GCP workflow execution: {response.name}")
        return response.name

    def get_execution_status(self, execution_name: str) -> dict:
        execution = self.client.get_execution(name=execution_name)
        
        state_map = {
            1: "ACTIVE",
            2: "SUCCEEDED",
            3: "FAILED",
            4: "CANCELLED"
        }
        
        status_info = {
            "state": state_map.get(execution.state, "UNKNOWN"),
            "error": execution.error.message if execution.error else None,
            "result": None
        }

        if execution.state == 2:  # SUCCEEDED
            status_info["result"] = json.loads(execution.result)

        return status_info

    def enqueue_polling_task(self, execution_name: str, task_id: str):
        """
        Enqueues a GCP Cloud Task to poll the workflow execution at the dedicated url.
        """
        is_prod = os.getenv("DJANGO_ENV", "development").lower() == "production"
        if not is_prod:
            return

        from google.cloud import tasks_v2
        
        project = os.getenv("GCP_PROJECT_ID", "animetix-prod")
        queue = os.getenv("GCP_TASKS_QUEUE_NAME", "animetix-queue")
        location = os.getenv("GCP_TASKS_LOCATION", "europe-west1")
        
        # Build the exact url for poll-workflow view
        base_worker_url = os.getenv("GCP_TASKS_WORKER_URL", "https://missawb-animetix-web.hf.space/api/tasks/run/")
        url = base_worker_url.replace("/api/tasks/run/", "/api/tasks/poll-workflow/")
        service_account = os.getenv("GCP_TASKS_SERVICE_ACCOUNT", "animetix-tasks-invoker@animetix.iam.gserviceaccount.com")
        
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        
        payload = {
            "execution_name": execution_name,
            "task_id": task_id
        }
        
        task_headers = {"Content-type": "application/json"}
        try:
            from animetix.telemetry import inject_trace_context
            inject_trace_context(task_headers)
        except ImportError:
            pass
            
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": task_headers,
                "body": json.dumps(payload).encode("utf-8"),
                "oidc_token": {
                    "service_account_email": service_account,
                    "audience": url
                }
            }
        }
        
        logger.info(f"Enqueuing polling task for {execution_name} to URL: {url}")
        client.create_task(request={"parent": parent, "task": task})

