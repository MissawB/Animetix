import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from animetix.api.cognition import ArchetypeNexusView, AIDebateArenaView, NeuroMemoryManagementView

def test_archetype_nexus_view_unauthenticated():
    factory = RequestFactory()
    request = factory.get('/api/v1/cognition/archetype-nexus/')
    view = ArchetypeNexusView.as_view()
    response = view(request)
    assert response.status_code in [401, 403]

def test_archetype_nexus_view_authenticated():
    factory = RequestFactory()
    request = factory.get('/api/v1/cognition/archetype-nexus/')
    user = MagicMock()
    user.id = 1
    user.is_authenticated = True
    request.user = user

    with patch('animetix.api.cognition.ArchetypeDriftSnapshot.objects.filter'), \
         patch('animetix.api.cognition.ArchetypeDriftSnapshot.objects.create'), \
         patch('animetix.api.cognition.get_container') as mock_get_container:
         
        mock_container = MagicMock()
        mock_container.core.archetype_drift_service.return_value.calculate_drift.return_value = MagicMock(
            archetype_id='The Sage', primary_accent='blue', aura_type='calm', aura_intensity=0.8, font_vibe='serif'
        )
        mock_container.core.neuro_symbolic_user_profiler.return_value.deduce_preference_rules.return_value = ['Likes action']
        mock_container.persistence.feedback_adapter.return_value.get_user_feedback.return_value = [{'input_context': 'test', 'is_positive': True}]
        mock_get_container.return_value = mock_container

        with patch.object(ArchetypeNexusView, 'permission_classes', []):
            from rest_framework.test import force_authenticate
            view = ArchetypeNexusView.as_view()
            force_authenticate(request, user=user)
            response = view(request)
            
            assert response.status_code == 200
            assert response.data['archetype']['id'] == 'The Sage'
            assert response.data['logical_rules'] == ['Likes action']
            assert len(response.data['recent_signals']) == 1

def test_ai_debate_arena_view():
    factory = RequestFactory()
    request = factory.post('/api/v1/cognition/debate-arena/', {'media_title': 'Naruto', 'topic': 'Best Ninja'}, content_type='application/json')
    user = MagicMock()
    user.is_authenticated = True
    request.user = user

    with patch('animetix.api.cognition.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_container.core.self_play_debate_service.return_value.run_debate.return_value = {"status": "success", "debate": "Naruto vs Sasuke"}
        mock_get_container.return_value = mock_container

        with patch.object(AIDebateArenaView, 'permission_classes', []):
            from rest_framework.test import force_authenticate
            view = AIDebateArenaView.as_view()
            force_authenticate(request, user=user)
            response = view(request)
            
            assert response.status_code == 200
            assert response.data['status'] == 'success'
            assert response.data['debate'] == 'Naruto vs Sasuke'

def test_neuro_memory_management_view_get():
    factory = RequestFactory()
    request = factory.get('/api/v1/cognition/neuro-memory/')
    user = MagicMock()
    user.id = 1
    user.is_authenticated = True
    request.user = user

    with patch('animetix.api.cognition.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_container.core.neuro_symbolic_user_profiler.return_value.deduce_preference_rules.return_value = ['Rule 1', 'Rule 2']
        mock_container.persistence.feedback_adapter.return_value.get_user_feedback.return_value = [{}, {}]
        mock_get_container.return_value = mock_container

        with patch.object(NeuroMemoryManagementView, 'permission_classes', []):
            from rest_framework.test import force_authenticate
            view = NeuroMemoryManagementView.as_view()
            force_authenticate(request, user=user)
            response = view(request)
            
            assert response.status_code == 200
            assert response.data['status'] == 'success'
            assert len(response.data['deduced_rules']) == 2
            assert response.data['total_signals'] == 2

def test_neuro_memory_management_view_post():
    factory = RequestFactory()
    request = factory.post('/api/v1/cognition/neuro-memory/', {'action': 'reset'}, content_type='application/json')
    user = MagicMock()
    user.is_authenticated = True
    request.user = user

    with patch.object(NeuroMemoryManagementView, 'permission_classes', []):
        from rest_framework.test import force_authenticate
        view = NeuroMemoryManagementView.as_view()
        force_authenticate(request, user=user)
        response = view(request)
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert response.data['message'] == 'Neuro-Symbolic profile reset.'
