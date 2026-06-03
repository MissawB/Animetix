# Design Document: PostgreSQL IAM Direct Authentication (Passwordless)

**Date:** 2026-06-03
**Topic:** Configuring Django database connection to Google Cloud SQL using IAM Direct authentication with temporary OAuth2 access tokens instead of static passwords.

## 1. Goal Description

Transition database connections to Cloud SQL from using static, hardcoded credentials to using IAM database authentication. The application's service account will act as the database user, and Django will dynamically generate a short-lived OAuth2 access token to authenticate every new connection.

This eliminates password secrets storage requirements and hardens database access security.

## 2. User Review Required

> [!IMPORTANT]
> - **Local Development Fallback:** In local development (`IS_PRODUCTION = False`), standard password-based authentication (SQLite or standard TCP PostgreSQL) will be used by default to prevent authentication failures when not running inside a Google Cloud environment.
> - **Service Account Username:** PostgreSQL role names for IAM users must be the service account email. Cloud SQL handles authentication matching the token audience.

## 3. Proposed Changes

We will introduce a custom Django database engine subclassing the standard PostgreSQL engine.

### Django Custom Database Engine

#### [NEW] [base.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/db/postgresql/base.py)
Create a new Django database wrapper:
- Inherit from `django.db.backends.postgresql.base.DatabaseWrapper`.
- Override `get_new_connection(self, conn_params)`.
- If `settings.DJANGO_DB_USE_IAM` is True, fetch a Google Cloud OAuth2 token using `google.auth.default(scopes=["https://www.googleapis.com/auth/sqlservice.admin"])`.
- Assign the refreshed token as `conn_params['password']`.
- Delegate connection establishment to psycopg2 via super class.

### Settings Configuration

#### [MODIFY] [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py)
- Detect database connection settings:
  - If `DJANGO_DB_USE_IAM` is enabled, configure `'ENGINE': 'animetix.db.postgresql'`.
  - Override `DATABASES['default']['USER']` with the IAM Service Account Email address (configured via env `GCP_TASKS_SERVICE_ACCOUNT` or similar).

## 4. Verification Plan

### Automated Tests
- Write a unit test mocking `google.auth.default` and verifying that `DatabaseWrapper.get_new_connection` generates a token and updates the connection password parameters dynamically.
