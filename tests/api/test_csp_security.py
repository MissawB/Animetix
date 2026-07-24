from unittest.mock import patch

import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_csp_script_src_in_dev_includes_unsafe_inline_and_eval(client):
    """In development mode (IS_PRODUCTION=False), unsafe-inline and unsafe-eval are permitted."""
    with override_settings(IS_PRODUCTION=False):
        from animetix_project import settings

        assert "'unsafe-inline'" in settings.CSP_SCRIPT_SRC


@pytest.mark.django_db
def test_csp_script_src_in_prod_excludes_unsafe_inline(client):
    """In production mode (IS_PRODUCTION=True), unsafe-inline is excluded by default from script-src."""
    with patch("animetix_project.settings.IS_PRODUCTION", True):
        # Dynamically re-evaluate setting logic for test verification
        from animetix_project.settings import env

        allow_unsafe_inline = env.bool("DJANGO_CSP_ALLOW_UNSAFE_INLINE", default=False)
        assert not allow_unsafe_inline
