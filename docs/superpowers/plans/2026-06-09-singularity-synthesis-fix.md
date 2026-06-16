# Task 1: Backend - Multiverse Synthesis Endpoint Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the Singularity Multiverse Synthesis endpoint to ensure universes are persisted for HITL validation and update the API tests with the correct URL.

**Architecture:** Modify the Django REST Framework view to call the domain service's persistence method and update the corresponding API test suite.

**Tech Stack:** Python, Django REST Framework, Pytest

---

### Task 1: Fix Backend Logic in labs.py

**Files:**
- Modify: `backend/api/animetix/api/labs.py`

- [ ] **Step 1: Add persistence call and update response**

Modify the `synthesize` action in `SingularityLabDataView.post`.

```python
<<<<
        elif action == 'synthesize':
            deduct_berrix(request.user, 100, "Singularity: Synthèse Multivers")
            universe_name = request.data.get('universe_name', 'Unnamed Universe')
            genre = request.data.get('genre', 'Cyberpunk')
            
            try:
                synthesizer = container.core.autonomous_domain_synthesizer()
                universe_data = synthesizer.synthesize_multiverse(
                    universe_name=universe_name, 
                    primary_genre=genre
                )
                evaluation = synthesizer.evaluate_coherence_and_interest(universe_data)
                
                return Response({
                    'status': 'success',
                    'universe': universe_data,
                    'evaluation': evaluation,
                    'message': f"Univers '{universe_name}' synthétisé et persisté."
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)
====
        elif action == 'synthesize':
            deduct_berrix(request.user, 100, "Singularity: Synthèse Multivers")
            universe_name = request.data.get('universe_name', 'Unnamed Universe')
            genre = request.data.get('genre', 'Cyberpunk')
            
            try:
                synthesizer = container.core.autonomous_domain_synthesizer()
                universe_data = synthesizer.synthesize_multiverse(
                    universe_name=universe_name, 
                    primary_genre=genre
                )
                
                # CRITICAL: Persist for HITL validation
                persisted = synthesizer.persist_universe_to_graph(universe_data)
                
                evaluation = synthesizer.evaluate_coherence_and_interest(universe_data)
                
                return Response({
                    'status': 'success',
                    'universe': universe_data,
                    'evaluation': evaluation,
                    'persisted': persisted,
                    'message': f"Univers '{universe_name}' synthétisé et stagé pour validation." if persisted else f"Univers '{universe_name}' synthétisé mais rejeté par les filtres de cohérence."
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)
>>>>
```

### Task 2: Restore and Fix API Tests

**Files:**
- Create: `tests/api/test_singularity_api.py`
- Delete: `tests/api/test_singularity_api.py.bak`

- [ ] **Step 1: Restore and update test file**

Create `tests/api/test_singularity_api.py` with the correct URL `/api/v1/singularity-lab/` and updated assertions.

```python
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_user(api_client, db):
    user = User.objects.create_user(username='testuser', password='password')
    api_client.force_authenticate(user=user)
    return user

@pytest.mark.django_db
def test_singularity_synthesize_success(api_client, authenticated_user):
    url = '/api/v1/singularity-lab/'
    payload = {
        'action': 'synthesize',
        'universe_name': 'NeonGenesisX',
        'genre': 'Sci-Fi'
    }
    
    with patch('animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_synthesizer = MagicMock()
        
        # Mock universe data
        universe_data = {
            "name": "NeonGenesisX",
            "genre": "Sci-Fi",
            "characters": [{"name": "Shinji"}],
            "episodes": [{"summary": "Test episode"}]
        }
        mock_synthesizer.synthesize_multiverse.return_value = universe_data
        mock_synthesizer.persist_universe_to_graph.return_value = True
        
        # Mock evaluation
        evaluation = {
            "is_worthy": True,
            "ai_score": 0.85,
            "community_score": 0.8,
            "reasoning": "Highly coherent."
        }
        mock_synthesizer.evaluate_coherence_and_interest.return_value = evaluation
        
        mock_container.core.autonomous_domain_synthesizer.return_value = mock_synthesizer
        mock_get_container.return_value = mock_container
        
        with patch('animetix.api.labs.deduct_berrix') as mock_deduct:
            response = api_client.post(url, payload, format='json')
            
            assert response.status_code == 200
            assert response.data['status'] == 'success'
            assert response.data['universe']['name'] == 'NeonGenesisX'
            assert response.data['evaluation']['is_worthy'] is True
            assert response.data['persisted'] is True
            assert "synthétisé et stagé pour validation" in response.data['message']
            
            # Verify calls
            mock_deduct.assert_called_once_with(authenticated_user, 100, "Singularity: Synthèse Multivers")
            mock_synthesizer.synthesize_multiverse.assert_called_once_with(
                universe_name='NeonGenesisX', 
                primary_genre='Sci-Fi'
            )
            mock_synthesizer.persist_universe_to_graph.assert_called_once_with(universe_data)
            mock_synthesizer.evaluate_coherence_and_interest.assert_called_once_with(universe_data)

@pytest.mark.django_db
def test_singularity_synthesize_error(api_client, authenticated_user):
    url = '/api/v1/singularity-lab/'
    payload = {
        'action': 'synthesize',
        'universe_name': 'NeonGenesisX'
    }
    
    with patch('animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_synthesizer = MagicMock()
        
        mock_synthesizer.synthesize_multiverse.side_effect = Exception("Synthesis failed")
        mock_container.core.autonomous_domain_synthesizer.return_value = mock_synthesizer
        mock_get_container.return_value = mock_container
        
        with patch('animetix.api.labs.deduct_berrix'):
            response = api_client.post(url, payload, format='json')
            
            assert response.status_code == 500
            assert response.data['error'] == 'Synthesis failed'

@pytest.mark.django_db
def test_singularity_unknown_action(api_client, authenticated_user):
    url = '/api/v1/singularity-lab/'
    payload = {'action': 'invalid'}
    response = api_client.post(url, payload, format='json')
    assert response.status_code == 400
    assert response.data['error'] == 'Action inconnue'
```

- [ ] **Step 2: Remove old .bak file**

Run: `rm tests/api/test_singularity_api.py.bak`

### Task 3: Verification

**Files:**
- N/A

- [ ] **Step 1: Run pipeline tests**

Run: `pytest tests/pipeline/test_singularity.py`
Expected: PASS

- [ ] **Step 2: Run API tests**

Run: `pytest tests/api/test_singularity_api.py`
Expected: PASS

### Task 4: Commit

- [ ] **Step 1: Commit work**

```bash
git add backend/api/animetix/api/labs.py tests/api/test_singularity_api.py
git commit -m "fix(singularity): ensure multiverses are persisted for HITL validation and fix API test URL"
```
