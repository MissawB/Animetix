# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError

# Setup path to backend
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
api_path = os.path.join(backend_path, "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)


class TestSQLDataQualityPipeline(unittest.TestCase):
    def test_run_command_generates_profiles_and_runs(self):
        # We test django command execution with mock subprocess to verify target routes
        with patch("subprocess.run") as mock_run:
            # Setup mock outputs
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_run.return_value = mock_res

            # Run command
            call_command("run_data_quality_tests", exclude_bigquery=True)

            # Verify subprocess ran dbt test on relational target
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("test", args)
            self.assertIn("dev", args)

    def test_command_failure_raises_error(self):
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.returncode = 1
            mock_res.stdout = "Failed test details"
            mock_res.stderr = "Errors"
            mock_run.return_value = mock_res

            with self.assertRaises(CommandError):
                call_command("run_data_quality_tests", exclude_bigquery=True)

    @patch("pipeline.mlops.rlhf_pipeline.run_sql_quality_checks")
    def test_pipeline_integration_runs_checks_first(self, mock_checks):
        from pipeline.mlops.rlhf_pipeline import (  # noqa: E402
            validated_dpo_dataset,
        )

        mock_feedback = {
            "feedback": "dummy_path.jsonl",
            "sessions": "dummy_sessions.jsonl",
        }

        with patch("pipeline.mlops.rlhf_pipeline.DPOFeedbackLoop") as mock_loop_class:
            mock_loop = MagicMock()
            mock_loop.process_and_export.return_value = 10
            mock_loop_class.return_value = mock_loop

            res = validated_dpo_dataset(mock_feedback)

            # Assert quality checks executed before compiling loop
            mock_checks.assert_called_once()
            self.assertEqual(res["count"], 10)
