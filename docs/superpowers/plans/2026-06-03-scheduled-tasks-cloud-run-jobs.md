# Scheduled Tasks with Cloud Run Jobs & Cloud Scheduler

Implement scheduled tasks on Google Cloud Platform to run maintenance and ETL commands, specifically the Django `sync_catalog` management command, on a daily basis.

## Goal
Set up a Cloud Run Job to execute `python backend/api/manage.py sync_catalog` and configure a Cloud Scheduler job to trigger it daily at 2:00 AM Europe/Paris.

## Steps
1. Enable `cloudscheduler.googleapis.com` API.
2. Deploy the Cloud Run Job `animetix-sync-catalog` with production secrets, environment variables, and VPC configuration matching the web service.
3. Deploy the Cloud Scheduler Job `animetix-sync-catalog-trigger` with OAuth authentication using the default compute service account.
4. Verify execution of the job and database sync.
