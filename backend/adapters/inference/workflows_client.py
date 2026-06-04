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
