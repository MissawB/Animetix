# -*- coding: utf-8 -*-
import os
import sys
import yaml
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Generates dbt profiles.yml dynamically and runs database quality tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude-bigquery",
            action="store_true",
            help="Exclude BigQuery telemetry tests from the run (useful for offline/local environments)",
        )

    def handle(self, *args, **options):
        # 1. Identify paths
        base_dir = settings.BASE_DIR
        # settings.BASE_DIR is backend/api, so os.path.dirname(base_dir) is backend/
        dbt_project_dir = os.path.join(
            os.path.dirname(base_dir), "pipeline", "dbt_project"
        )

        # 2. Determine Relational DB parameters
        db_settings = settings.DATABASES["default"]
        engine = db_settings["ENGINE"]

        relational_output = {}
        if "sqlite" in engine:
            db_path = db_settings["NAME"]
            # Convert to absolute path
            if not os.path.isabs(str(db_path)):
                db_path = os.path.abspath(os.path.join(base_dir, str(db_path)))

            schema_dir = os.path.join(dbt_project_dir, "sqlite_schemas")
            os.makedirs(schema_dir, exist_ok=True)

            relational_output = {
                "type": "sqlite",
                "threads": 1,
                "database": "main",
                "schema": "main",
                "schemas_and_paths": {"main": str(db_path)},
                "schema_directory": schema_dir,
            }

            self.stdout.write(
                self.style.WARNING(f"Configuring dbt for SQLite at: {db_path}")
            )
        elif "postgresql" in engine or "postgis" in engine:
            relational_output = {
                "type": "postgres",
                "host": db_settings.get("HOST", "localhost"),
                "user": db_settings.get("USER", "postgres"),
                "pass": db_settings.get("PASSWORD", ""),
                "port": int(db_settings.get("PORT", 5432) or 5432),
                "dbname": db_settings.get("NAME", "animetix"),
                "schema": "public",
                "threads": 1,
            }
            self.stdout.write(
                self.style.WARNING(
                    f"Configuring dbt for PostgreSQL database: {relational_output['dbname']}"
                )
            )
        else:
            raise CommandError(f"Unsupported database engine for dbt tests: {engine}")

        # 3. Determine BigQuery parameters (Telemetry)
        bq_output = {
            "type": "bigquery",
            "method": "oauth",  # fallback to OAuth or Application Default Credentials (ADC)
            "project": getattr(settings, "GCP_PROJECT_ID", "animetix-project"),
            "dataset": getattr(settings, "GCP_BIGQUERY_DATASET", "telemetry"),
            "threads": 1,
        }

        # Write config
        profiles_content = {
            "animetix_quality": {
                "target": "dev",
                "outputs": {"dev": relational_output, "bigquery": bq_output},
            }
        }

        profiles_path = os.path.join(dbt_project_dir, "profiles.yml")
        with open(profiles_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(profiles_content, f, default_flow_style=False)

        self.stdout.write(
            self.style.SUCCESS(f"Generated dynamic profiles.yml at: {profiles_path}")
        )

        # Resolve dbt executable from virtual environment
        dbt_exe = "dbt"
        venv_dbt_win = os.path.join(sys.prefix, "Scripts", "dbt.exe")
        venv_dbt_nix = os.path.join(sys.prefix, "bin", "dbt")
        if os.path.exists(venv_dbt_win):
            dbt_exe = venv_dbt_win
        elif os.path.exists(venv_dbt_nix):
            dbt_exe = venv_dbt_nix

        # 4. Run tests
        # A. Relational tests (target: dev)
        self.stdout.write("Running dbt tests on Relational Database...")
        cmd_relational = [
            dbt_exe,
            "test",
            "--project-dir",
            dbt_project_dir,
            "--profiles-dir",
            dbt_project_dir,
            "--target",
            "dev",
            "--select",
            "source:django_source",
        ]

        res_rel = subprocess.run(cmd_relational, capture_output=True, text=True)
        if res_rel.returncode != 0:
            self.stdout.write(self.style.ERROR(res_rel.stdout))
            self.stdout.write(self.style.ERROR(res_rel.stderr))
            raise CommandError(
                "[FAIL] Relational SQL database data quality tests failed."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "[SUCCESS] Relational database data quality checks passed."
                )
            )

        # B. Telemetry tests (target: bigquery)
        if not options["exclude_bigquery"]:
            self.stdout.write("Running dbt tests on BigQuery Telemetry...")
            cmd_bq = [
                dbt_exe,
                "test",
                "--project-dir",
                dbt_project_dir,
                "--profiles-dir",
                dbt_project_dir,
                "--target",
                "bigquery",
                "--select",
                "source:telemetry_source archetype_drift_values_check",
            ]
            res_bq = subprocess.run(cmd_bq, capture_output=True, text=True)
            if res_bq.returncode != 0:
                self.stdout.write(self.style.ERROR(res_bq.stdout))
                self.stdout.write(self.style.ERROR(res_bq.stderr))
                raise CommandError(
                    "[FAIL] BigQuery Telemetry database data quality tests failed."
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "[SUCCESS] BigQuery Telemetry database data quality checks passed."
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping BigQuery Telemetry tests (exclude flag set)."
                )
            )
