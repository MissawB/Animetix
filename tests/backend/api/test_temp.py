import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_reverse_clubs():
    try:
        url = reverse('api-clubs')
        print(f"URL found: {url}")
    except Exception as e:
        pytest.fail(f"Could not reverse 'api-clubs': {e}")
