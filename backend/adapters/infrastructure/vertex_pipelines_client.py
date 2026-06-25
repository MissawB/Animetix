import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Optional

from django.conf import settings

logger = logging.getLogger("animetix.mlops.pipelines")

try:
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import aiplatform

    HAS_PLATFORM = True
except ImportError:
    HAS_PLATFORM = False

try:
    from kfp import compiler

    HAS_KFP = True
except ImportError:
    HAS_KFP = False


class VertexPipelinesClient:
    def __init__(self):
        self.project_id = getattr(settings, "GCP_PROJECT_ID", "animetix")
        self.region = getattr(settings, "VERTEX_AI_PIPELINE_REGION", "europe-west1")
        self.pipeline_root = getattr(
            settings,
            "VERTEX_AI_PIPELINE_ROOT",
            "gs://animetix-vertex-pipelines-staging/",
        )
        self.service_account = getattr(
            settings,
            "VERTEX_AI_PIPELINE_SA",
            "animetix-vertex-sa@animetix.iam.gserviceaccount.com",
        )

        self.simulation_mode = (
            os.getenv("VERTEX_AI_SIMULATION", "false").lower() == "true"
        )

        # Determine simulation mode if credentials are not available or HAS_PLATFORM is False
        if not HAS_PLATFORM or not HAS_KFP:
            self.simulation_mode = True
            logger.info(
                "Vertex AI Platform or KFP not installed. Running in simulation mode."
            )
        else:
            try:
                # Attempt to initialize aiplatform
                aiplatform.init(
                    project=self.project_id,
                    location=self.region,
                    staging_bucket=self.pipeline_root,
                )
                logger.info("Initialized Vertex AI Platform client.")
            except (DefaultCredentialsError, Exception) as e:
                self.simulation_mode = True
                logger.warning(
                    f"Failed to initialize Vertex AI client due to credentials or connection error ({e}). Falling back to simulation mode."
                )

        # Path for keeping simulated runs in a local JSON file (useful for testing & local development)
        self.mock_runs_path = os.path.join(
            getattr(settings, "DATA_DIR", tempfile.gettempdir()),
            "vertex_pipelines_mock_runs.json",
        )

    def submit_pipeline(
        self,
        pipeline_func,
        pipeline_name: str,
        parameter_values: Optional[dict] = None,
        enable_caching: bool = True,
    ) -> dict:
        """
        Compiles the KFP pipeline function to YAML and submits it as a PipelineJob to Vertex AI.
        """
        parameter_values = parameter_values or {}

        # 1. Compile the pipeline to verify correctness (even in simulation mode)
        if not HAS_KFP:
            logger.error("KFP is required to compile and run pipelines.")
            raise ImportError("Kubeflow Pipelines (kfp) SDK is not installed.")

        fd, temp_yaml_path = tempfile.mkstemp(suffix=".yaml")
        try:
            os.close(fd)
            # Compile KFP pipeline function to local YAML file
            compiler.Compiler().compile(
                pipeline_func=pipeline_func, package_path=temp_yaml_path
            )
            logger.info(
                f"Successfully compiled KFP pipeline {pipeline_name} to {temp_yaml_path}"
            )
        except Exception as e:
            logger.error(f"Failed to compile pipeline {pipeline_name}: {e}")
            raise ValueError(f"Pipeline compilation failed: {e}")
        finally:
            try:
                os.remove(temp_yaml_path)
            except OSError:
                pass

        # 2. Submit pipeline
        if self.simulation_mode:
            logger.info(
                f"[SIMULATION] Submitting pipeline {pipeline_name} with params: {parameter_values}"
            )

            # Generate a mock job ID and details
            job_id = f"mock-pipeline-run-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6]}"
            run_name = f"projects/{self.project_id}/locations/{self.region}/pipelineJobs/{job_id}"

            run_data = {
                "name": run_name,
                "display_name": pipeline_name,
                "pipeline_name": pipeline_name,
                "state": "PIPELINE_STATE_RUNNING",
                "create_time": datetime.now(timezone.utc).isoformat(),
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": None,
                "update_time": datetime.now(timezone.utc).isoformat(),
                "parameter_values": parameter_values,
                "enable_caching": enable_caching,
                "service_account": self.service_account,
                "labels": {"env": "development", "triggered-by": "django-mlops"},
                "error": None,
            }

            self._save_mock_run(run_data)
            return run_data

        try:
            # Real submission to Vertex AI
            job = aiplatform.PipelineJob(
                display_name=pipeline_name,
                template_path=temp_yaml_path,
                pipeline_root=self.pipeline_root,
                parameter_values=parameter_values,
                enable_caching=enable_caching,
            )
            job.submit(service_account=self.service_account)

            logger.info(
                f"Successfully submitted Vertex AI PipelineJob: {job.name} (state: {job.state})"
            )

            return {
                "name": job.resource_name,
                "display_name": job.display_name,
                "state": str(job.state),
                "create_time": job.create_time.isoformat() if job.create_time else None,
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "update_time": job.update_time.isoformat() if job.update_time else None,
                "parameter_values": parameter_values,
                "enable_caching": enable_caching,
                "service_account": self.service_account,
                "labels": dict(job.labels) if job.labels else {},
                "error": str(job.error) if job.error else None,
            }
        except Exception as e:
            logger.error(f"Failed to submit Vertex AI PipelineJob {pipeline_name}: {e}")
            raise e

    def get_pipeline_run(self, pipeline_job_name: str) -> dict:
        """
        Retrieves the status of a specific pipeline run.
        """
        if self.simulation_mode:
            runs = self._load_mock_runs()
            # The input might be the full resource name or just the job ID
            for run in runs:
                if run["name"] == pipeline_job_name or pipeline_job_name in run["name"]:
                    # Transition run to SUCCEEDED dynamically if it's been a while (simulation)
                    if run["state"] == "PIPELINE_STATE_RUNNING":
                        # For simulation purposes, make it complete
                        run["state"] = "PIPELINE_STATE_SUCCEEDED"
                        run["end_time"] = datetime.now(timezone.utc).isoformat()
                        self._save_mock_run(run)
                    return run
            return {"error": f"Pipeline run {pipeline_job_name} not found."}

        try:
            job = aiplatform.PipelineJob.get(resource_name=pipeline_job_name)
            return {
                "name": job.resource_name,
                "display_name": job.display_name,
                "state": str(job.state),
                "create_time": job.create_time.isoformat() if job.create_time else None,
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "update_time": job.update_time.isoformat() if job.update_time else None,
                "parameter_values": (
                    dict(job.runtime_config.parameter_values)
                    if job.runtime_config
                    else {}
                ),
                "service_account": job.service_account,
                "labels": dict(job.labels) if job.labels else {},
                "error": str(job.error) if job.error else None,
            }
        except Exception as e:
            logger.error(f"Failed to retrieve pipeline run {pipeline_job_name}: {e}")
            return {"error": str(e)}

    def list_pipeline_runs(
        self, pipeline_name: Optional[str] = None, limit: int = 20
    ) -> list:
        """
        Lists recent pipeline runs with lineage/state metadata.
        """
        if self.simulation_mode:
            runs = self._load_mock_runs()
            if pipeline_name:
                runs = [
                    r
                    for r in runs
                    if pipeline_name.lower() in r["display_name"].lower()
                ]
            # Sort by create_time descending
            runs.sort(key=lambda x: x.get("create_time", ""), reverse=True)
            return runs[:limit]

        try:
            # Query pipeline jobs using Vertex AI Platform
            filter_str = None
            if pipeline_name:
                filter_str = f'display_name="{pipeline_name}"'

            jobs = aiplatform.PipelineJob.list(
                filter=filter_str, order_by="create_time desc"
            )

            results = []
            for job in jobs[:limit]:
                results.append(
                    {
                        "name": job.resource_name,
                        "display_name": job.display_name,
                        "state": str(job.state),
                        "create_time": (
                            job.create_time.isoformat() if job.create_time else None
                        ),
                        "start_time": (
                            job.start_time.isoformat() if job.start_time else None
                        ),
                        "end_time": job.end_time.isoformat() if job.end_time else None,
                        "update_time": (
                            job.update_time.isoformat() if job.update_time else None
                        ),
                        "parameter_values": (
                            dict(job.runtime_config.parameter_values)
                            if job.runtime_config
                            else {}
                        ),
                        "labels": dict(job.labels) if job.labels else {},
                        "error": str(job.error) if job.error else None,
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Failed to list pipeline runs: {e}")
            return []

    def _load_mock_runs(self) -> list:
        if not os.path.exists(self.mock_runs_path):
            return []
        try:
            with open(self.mock_runs_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_mock_run(self, run_data: dict):
        runs = self._load_mock_runs()

        # Replace if exists
        updated = False
        for idx, run in enumerate(runs):
            if run["name"] == run_data["name"]:
                runs[idx] = run_data
                updated = True
                break

        if not updated:
            runs.append(run_data)

        # Ensure parent directories exist
        os.makedirs(os.path.dirname(self.mock_runs_path), exist_ok=True)
        try:
            with open(self.mock_runs_path, "w", encoding="utf-8") as f:
                json.dump(runs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save mock pipeline runs: {e}")
