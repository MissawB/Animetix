# Finalisation Intégration Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Désorpheliniser la page Explorer en ajoutant des recommandations personnalisées et en améliorant la navigation contextuelle.

**Architecture:** 
- Le backend enrichit la réponse de `MediaExploreView` avec les données de `UserRecommendation`.
- Le frontend affiche une nouvelle rangée "Choisi pour vous" en haut de la page.
- La page de détails redirige désormais vers le Nexus (`/explore/`).

**Tech Stack:** Django (DRF), React (TypeScript), Tailwind CSS, TanStack Query.

---

### Task 1: Mise à jour du Backend (API & Tests)

**Files:**
- Create: `tests/api/test_explore.py`
- Modify: `backend/api/animetix/api/explore.py`

- [ ] **Step 1: Créer le test pour les recommandations personnalisées**

```python
import pytest
from django.urls import reverse
from rest_framework import status
from animetix.models import UserRecommendation, MediaItem
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_media_explore_view_recommendations(client):
    user = User.objects.create_user(username='testuser', password='password')
    client.force_authenticate(user=user)
    
    # Créer un media et une recommandation
    media = MediaItem.objects.create(id="test-1", title="Test Media", media_type="Anime")
    UserRecommendation.objects.create(user=user, media_item=media, score=0.9, rank=1)
    
    url = reverse('api_explore')
    response = client.get(url, {'media_type': 'Anime'})
    
    assert response.status_code == status.status.HTTP_200_OK
    assert 'recommendations' in response.data
    assert len(response.data['recommendations']) > 0
    assert response.data['recommendations'][0]['id'] == "test-1"
```

- [ ] **Step 2: Exécuter le test pour vérifier l'échec**

Exécuter : `pytest tests/api/test_explore.py`
Attendu : Échec (car `recommendations` n'est pas encore dans la réponse).

- [ ] **Step 3: Implémenter la logique de recommandation dans la vue**

```python
# Modifier backend/api/animetix/api/explore.py
# Ajouter UserRecommendation aux imports si nécessaire
from ..models import MediaItem, UserRecommendation

# Dans MediaExploreView.get :
        recommendations = []
        if request.user.is_authenticated:
            user_recs = UserRecommendation.objects.filter(
                user=request.user, 
                media_item__media_type=media_type
            ).select_related('media_item').order_by('rank')[:10]
            
            recommendations = [
                {
                    "id": rec.media_item.id,
                    "title": rec.media_item.title,
                    "image": rec.media_item.image,
                    "synopsis_fr": rec.media_item.synopsis_fr,
                    "is_recommendation": True
                } for rec in user_recs
            ]

        # Mettre à jour la réponse finale
        return response.Response({
            "trending": items,
            "recommendations": recommendations, # Ajouté ici
            "categories": [...]
        })
```

- [ ] **Step 4: Exécuter le test pour vérifier la réussite**

Exécuter : `pytest tests/api/test_explore.py`
Attendu : PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/api/test_explore.py backend/api/animetix/api/explore.py
git commit -m "feat(backend): add user recommendations to explore API"
```

### Task 2: Mise à jour du Frontend (Page Explorer)

**Files:**
- Modify: `frontend/src/features/explore/ExplorePage.tsx`

- [ ] **Step 1: Mettre à jour le type de données et l'UI pour la rangée de recommandations**

Ajouter la section "Choisi pour vous" juste après le Hero et avant les tendances.

```typescript
// frontend/src/features/explore/ExplorePage.tsx

{/* Recommendations Row */}
{data?.recommendations?.length > 0 && (
    <div className="space-y-4">
        <h2 className="text-2xl font-black italic uppercase tracking-widest flex items-center gap-3">
            Choisi pour vous
            <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded font-normal not-italic ml-2">IA : SUGGESTION</span>
            <span className="h-px bg-blue-500/30 flex-1" />
        </h2>
        <div className="relative group">
            <button 
                onClick={() => scrollLeft('recs-row')}
                className="absolute left-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
            >
                <ChevronLeft size={32} />
            </button>
            <div 
                id="recs-row"
                className="flex gap-6 overflow-x-auto no-scrollbar pb-4"
            >
                {data.recommendations.map((item: any) => (
                    <MediaCard key={item.id} item={item} />
                ))}
            </div>
            <button 
                onClick={() => scrollRight('recs-row')}
                className="absolute right-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
            >
                <ChevronRight size={32} />
            </button>
        </div>
    </div>
)}
```

- [ ] **Step 2: Vérifier visuellement (si possible) ou via les tests existants**

Exécuter les tests frontend : `npm test frontend/src/features/explore/__tests__/ExplorePage.test.tsx` (après mise à jour des mocks si nécessaire).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/explore/ExplorePage.tsx
git commit -m "feat(frontend): add recommendations row to Explore page"
```

### Task 3: Mise à jour de la Navigation Contextuelle

**Files:**
- Modify: `frontend/src/features/media/MediaDetailPage.tsx`

- [ ] **Step 1: Changer le lien de retour vers le Nexus**

```typescript
// frontend/src/features/media/MediaDetailPage.tsx

{/* Navigation */}
<Link to="/explore/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-12 no-underline group">
    <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Retour au Nexus
</Link>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/media/MediaDetailPage.tsx
git commit -m "feat(frontend): redirect back link to Explorer Nexus"
```
