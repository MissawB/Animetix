import os
import sys
import importlib
from unittest.mock import patch
from animetix_project import settings

def test_settings_db_config_with_tcp():
    test_url = "postgres://user:password@localhost:5432/dbname"
    with patch.dict(os.environ, {"DATABASE_URL": test_url, "DJANGO_ENV": "development"}):
        importlib.reload(settings)
        db_config = settings.DATABASES['default']
        assert db_config['OPTIONS'].get('sslmode') == 'require'

def test_settings_db_config_with_unix_socket():
    test_url = "postgres://user:password@/dbname?host=/cloudsql/project:region:instance"
    with patch.dict(os.environ, {"DATABASE_URL": test_url, "DJANGO_ENV": "development"}):
        importlib.reload(settings)
        db_config = settings.DATABASES['default']
        assert 'sslmode' not in db_config.get('OPTIONS', {})
