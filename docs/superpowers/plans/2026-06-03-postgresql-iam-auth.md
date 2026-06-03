# PostgreSQL IAM Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure Django connection to Google Cloud SQL using direct IAM authentication using temporary OAuth2 access tokens as passwords.

**Architecture:** 
- A custom database engine `animetix.db.postgresql` extending `django.db.backends.postgresql`.
- Dynamic Google OAuth2 access token generation inside `get_new_connection`.
- Activation controlled by setting `DJANGO_DB_USE_IAM`.

**Tech Stack:** Django, psycopg2, google-auth

---

### Task 1: Implement Custom PostgreSQL Database Wrapper

**Files:**
- Create: `backend/api/animetix/db/__init__.py`
- Create: `backend/api/animetix/db/postgresql/__init__.py`
- Create: `backend/api/animetix/db/postgresql/base.py`
- Test: `tests/backend/test_db_iam.py`

- [ ] **Step 1: Write the failing test**

Create `tests/backend/test_db_iam.py`:
```python
import pytest
from unittest.mock import MagicMock, patch

@patch('google.auth.default')
def test_custom_wrapper_generates_token(mock_auth, settings):
    # Setup mock credentials
    mock_credentials = MagicMock()
    mock_credentials.token = "mock-oauth2-access-token-123"
    mock_auth.return_value = (mock_credentials, "mock-project")
    
    # Import the custom DatabaseWrapper
    from animetix.db.postgresql.base import DatabaseWrapper
    
    settings.DJANGO_DB_USE_IAM = True
    
    wrapper = DatabaseWrapper(settings.DATABASES['default'])
    
    # Mock psycopg2 connection call
    with patch('django.db.backends.postgresql.base.DatabaseWrapper.get_new_connection') as mock_super_conn:
        conn_params = {'user': 'my-sa@project.iam', 'password': 'old'}
        wrapper.get_new_connection(conn_params)
        
        # Verify password got replaced by the refreshed token
        mock_credentials.refresh.assert_called_once()
        assert conn_params['password'] == "mock-oauth2-access-token-123"
        mock_super_conn.assert_called_once_with(conn_params)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/backend/test_db_iam.py -v`
Expected: FAIL (No database backend module found)

- [ ] **Step 3: Implement custom PostgreSQL wrapper**

Create `backend/api/animetix/db/postgresql/base.py`:
```python
import google.auth
import google.auth.transport.requests
from django.conf import settings
from django.db.backends.postgresql.base import DatabaseWrapper as PostgresDatabaseWrapper

class DatabaseWrapper(PostgresDatabaseWrapper):
    def get_new_connection(self, conn_params):
        use_iam = getattr(settings, 'DJANGO_DB_USE_IAM', False)
        
        if use_iam:
            try:
                # Retrieve the Google OAuth2 access token for IAM auth
                scopes = ["https://www.googleapis.com/auth/sqlservice.admin", "https://www.googleapis.com/auth/cloud-platform"]
                credentials, project = google.auth.default(scopes=scopes)
                auth_req = google.auth.transport.requests.Request()
                credentials.refresh(auth_req)
                
                # Set OAuth2 token as connection password
                conn_params['password'] = credentials.token
            except Exception as e:
                # Fallback logging if authentication token fetch fails
                import logging
                logger = logging.getLogger("django.db.backends")
                logger.error(f"Failed to fetch PostgreSQL IAM OAuth2 token: {e}")
                raise
                
        return super().get_new_connection(conn_params)
```

Create empty `__init__.py` files at:
- `backend/api/animetix/db/__init__.py`
- `backend/api/animetix/db/postgresql/__init__.py`

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/backend/test_db_iam.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add backend/api/animetix/db tests/backend/test_db_iam.py
git commit -m "feat: implement animetix.db.postgresql database wrapper with dynamic IAM token injection"
```

---

### Task 2: Configure Database Engine Settings

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Modify settings.py to conditionalize database engine**

Modify `backend/api/animetix_project/settings.py` database settings to set custom engine and service account username.
Look for:
```python
# Database
if os.getenv('DATABASE_URL'):
    DATABASES = {'default': env.db('DATABASE_URL')}
    ...
```
Replace it with:
```python
# Database
DJANGO_DB_USE_IAM = env.bool('DJANGO_DB_USE_IAM', default=IS_PRODUCTION)

if os.getenv('DATABASE_URL'):
    DATABASES = {'default': env.db('DATABASE_URL')}
    db_host = DATABASES['default'].get('HOST', '') or DATABASES['default'].get('OPTIONS', {}).get('host', '')
    if db_host.startswith('/') or 'cloudsql' in db_host:
        # Unix socket connection (GCP Cloud SQL). Do not set sslmode='require' as it is not supported/needed over Unix sockets.
        if 'OPTIONS' not in DATABASES['default']:
            DATABASES['default']['OPTIONS'] = {}
        if 'sslmode' in DATABASES['default']['OPTIONS']:
            del DATABASES['default']['OPTIONS']['sslmode']
    else:
        # Standard TCP connection, enforce SSL
        if 'OPTIONS' not in DATABASES['default']:
            DATABASES['default']['OPTIONS'] = {}
        DATABASES['default']['OPTIONS']['sslmode'] = 'require'
        
    if DJANGO_DB_USE_IAM:
        DATABASES['default']['ENGINE'] = 'animetix.db.postgresql'
        # In Cloud SQL IAM, the user is the service account email address
        DATABASES['default']['USER'] = env('GCP_TASKS_SERVICE_ACCOUNT', default='animetix-tasks-invoker@animetix.iam.gserviceaccount.com')
        DATABASES['default']['PASSWORD'] = ''  # Will be dynamically set by wrapper
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
DATABASES['default']['ATOMIC_REQUESTS'] = False
```

- [ ] **Step 2: Commit**

Run:
```bash
git add backend/api/animetix_project/settings.py
git commit -m "config: enable animetix.db.postgresql custom engine and IAM credentials when DJANGO_DB_USE_IAM is enabled"
```
