import pytest
from django.contrib.auth.models import User
from animetix.models import CreativeFusion

@pytest.mark.django_db
def test_creative_fusion_model_creation():
    user = User.objects.create_user(username="forger", password="pwd")
    parent = CreativeFusion.objects.create(
        title_a="Naruto", title_b="Cyberpunk", media_type_a="Anime", media_type_b="Anime",
        scenario_text="Test", creator=user
    )
    remix = CreativeFusion.objects.create(
        title_a="Naruto", title_b="Cyberpunk", media_type_a="Anime", media_type_b="Anime",
        scenario_text="Test Remix", creator=user, parent=parent, chaos_level=80
    )
    assert remix.parent == parent
    assert remix.chaos_level == 80

from unittest.mock import patch
from src.backend.animetix.tasks import generate_fusion_scenario_task

@patch('src.backend.animetix.tasks.get_container')
def test_generate_fusion_scenario_with_params(mock_get_container):
    mock_service = mock_get_container.return_value.llm_service
    mock_service.generate_fusion_scenario.return_value = "Test Scenario"
    
    result = generate_fusion_scenario_task(
        "Anime", {"title": "A"}, {"title": "B"}, "Français",
        chaos_level=80, universe_balance=20, art_style="Ghibli"
    )
    
    assert result == "Test Scenario"
    mock_service.generate_fusion_scenario.assert_called_once()
    # Check if params are passed
    kwargs = mock_service.generate_fusion_scenario.call_args[1]
    assert kwargs.get('chaos_level') == 80

from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
def test_archetypist_view_post_creates_fusion_placeholder():
    client = Client()
    # We mock the celery task chain to avoid real execution
    with patch('animetix.views.forge.chain') as mock_chain:
        # Mock animetix_service.load_data
        with patch('animetix.views.forge.animetix_service.load_data') as mock_load:
            mock_load.return_value = {
                'titles': ['Naruto', 'Bleach'],
                'title_to_full_data': {
                    'Naruto': {'id': 1, 'title': 'Naruto'},
                    'Bleach': {'id': 2, 'title': 'Bleach'}
                }
            }
            response = client.post(reverse('archetypist'), {
                'title_A': 'Naruto', 'title_B': 'Bleach',
                'media_type_A': 'Anime', 'media_type_B': 'Anime',
                'chaos_level': '80', 'universe_balance': '20', 'art_style': 'Ghibli'
            })
            assert response.status_code == 200
            # Check that a CreativeFusion was created
            assert CreativeFusion.objects.count() == 1
            fusion = CreativeFusion.objects.first()
            assert fusion.chaos_level == 80
            assert fusion.art_style == 'Ghibli'
