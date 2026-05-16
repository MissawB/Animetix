# Social Forge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Archetypist (Creative Forge) into a community-driven ecosystem with granular creative controls (chaos, balance, style) and social features (remixing, likes).

**Architecture:** We will create a new Django model `CreativeFusion` to persist generations. The `forge.py` view will be updated to handle the new UI parameters, saving the model instance, and triggering updated Celery tasks that inject these parameters into the LLM/Image prompts. The UI will use HTMX for smooth interactions.

**Tech Stack:** Django (ORM, Views), Celery (Async Tasks), HTMX, Tailwind CSS, PostgreSQL/SQLite.

---

### Task 1: Create `CreativeFusion` Model and API

**Files:**
- Modify: `src/backend/animetix/models.py`
- Modify: `src/backend/animetix/api_views.py`
- Modify: `src/backend/animetix/serializers.py`
- Create: `src/backend/animetix/migrations/` (via makemigrations)

- [ ] **Step 1: Write the failing test**

```python
# Create tests/backend/test_forge.py
import pytest
from django.contrib.auth.models import User
from src.backend.animetix.models import CreativeFusion

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backend/test_forge.py -v`
Expected: FAIL with `ImportError: cannot import name 'CreativeFusion'`

- [ ] **Step 3: Write minimal implementation in `models.py`**

```python
# In src/backend/animetix/models.py (add at the end)
from django.db import models
from django.contrib.auth.models import User

class CreativeFusion(models.Model):
    title_a = models.CharField(max_length=255)
    title_b = models.CharField(max_length=255)
    media_type_a = models.CharField(max_length=50)
    media_type_b = models.CharField(max_length=50)
    
    scenario_text = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    chaos_level = models.IntegerField(default=50)
    universe_balance = models.IntegerField(default=50)
    art_style = models.CharField(max_length=100, default='Cyberpunk')
    
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fusions')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='remixes')
    likes = models.ManyToManyField(User, related_name='liked_fusions', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title_a} x {self.title_b} by {self.creator}"
```

- [ ] **Step 4: Generate and apply migrations**

Run: `python src/backend/manage.py makemigrations animetix`
Run: `python src/backend/manage.py migrate`

- [ ] **Step 5: Add Serializer and ViewSet for Community Feed**

```python
# In src/backend/animetix/serializers.py (add at the end)
from rest_framework import serializers
from .models import CreativeFusion

class CreativeFusionSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    is_remix = serializers.BooleanField(source='parent_id', read_only=True)
    
    class Meta:
        model = CreativeFusion
        fields = '__all__'

# In src/backend/animetix/api_views.py (add at the end)
from rest_framework import viewsets
from .models import CreativeFusion
from .serializers import CreativeFusionSerializer

class CreativeFusionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CreativeFusion.objects.all().order_by('-created_at')
    serializer_class = CreativeFusionSerializer
    
# In src/backend/animetix/urls.py (add to router)
# router.register(r'fusions', api_views.CreativeFusionViewSet)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/backend/test_forge.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/backend/animetix/models.py src/backend/animetix/migrations/ src/backend/animetix/serializers.py src/backend/animetix/api_views.py src/backend/animetix/urls.py tests/backend/test_forge.py
git commit -m "feat: add CreativeFusion model and API endpoints"
```

---

### Task 2: Update Generation Tasks with Creative Parameters

**Files:**
- Modify: `src/backend/animetix/tasks.py`
- Modify: `src/backend/animetix/creative_tasks.py`
- Modify: `src/core/domain/services/llm_service.py` (or where the prompt is built)

- [ ] **Step 1: Write the failing test**

```python
# In tests/backend/test_forge.py
from unittest.mock import patch
from src.backend.animetix.tasks import generate_fusion_scenario_task

@patch('src.backend.animetix.tasks.get_container')
def test_generate_fusion_scenario_with_params(mock_get_container):
    mock_service = mock_get_container.return_value.animinator_service
    mock_service.llm_service.generate_fusion_scenario.return_value = "Test Scenario"
    
    result = generate_fusion_scenario_task(
        "Anime", {"title": "A"}, {"title": "B"}, "Français",
        chaos_level=80, universe_balance=20, art_style="Ghibli"
    )
    
    assert result == "Test Scenario"
    mock_service.llm_service.generate_fusion_scenario.assert_called_once()
    # Check if params are passed
    kwargs = mock_service.llm_service.generate_fusion_scenario.call_args[1]
    assert kwargs.get('chaos_level') == 80
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backend/test_forge.py::test_generate_fusion_scenario_with_params -v`
Expected: FAIL (unexpected keyword argument)

- [ ] **Step 3: Update `tasks.py` and `creative_tasks.py` signatures**

```python
# In src/backend/animetix/tasks.py (update generate_fusion_scenario_task)
@shared_task
def generate_fusion_scenario_task(media_type, item1, item2, language, chaos_level=50, universe_balance=50, art_style="Cyberpunk"):
    try:
        from .containers import get_container
        container = get_container()
        scenario = container.animinator_service.llm_service.generate_fusion_scenario(
            media_type, item1, item2, language, 
            chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style
        )
        return scenario
    except Exception as e:
        logger.error(f"Task Error: {e}")
        return "Erreur lors de la fusion."

# Note: Also update generate_fusion_image_task in tasks.py to accept art_style
@shared_task
def generate_fusion_image_task(item1, item2, art_style="Cyberpunk"):
    try:
        from .creative_tasks import generate_fusion_image
        return generate_fusion_image(item1, item2, art_style=art_style)
    except Exception as e:
        logger.error(f"Task Error: {e}")
        return None
```

- [ ] **Step 4: Update Domain Services (LLM Prompting)**

```python
# In src/core/domain/services/llm_service.py (update generate_fusion_scenario)
    def generate_fusion_scenario(self, media_type: str, item1: Dict, item2: Dict, language: str, chaos_level: int = 50, universe_balance: int = 50, art_style: str = "Cyberpunk") -> str:
        
        balance_instruction = ""
        if universe_balance < 40:
            balance_instruction = f"L'univers de {item1['title']} doit dominer."
        elif universe_balance > 60:
            balance_instruction = f"L'univers de {item2['title']} doit dominer."
        else:
            balance_instruction = "Les deux univers doivent être parfaitement équilibrés."
            
        chaos_instruction = "Garde un récit très logique et ancré dans le lore." if chaos_level < 30 else ("N'hésite pas à être abstrait et à briser le 4ème mur." if chaos_level > 70 else "Mélange les concepts de manière créative.")

        prompt = f"""
        Crée un pitch de 3 lignes pour un crossover entre "{item1['title']}" et "{item2['title']}".
        INSTRUCTIONS CREATIVES:
        - Style Visuel Cible: {art_style} (Adapte le vocabulaire du pitch à ce style)
        - Équilibre: {balance_instruction}
        - Niveau de Chaos ({chaos_level}/100): {chaos_instruction}
        Réponds en {language}.
        """
        # ... rest of the existing function
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/backend/test_forge.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/backend/animetix/tasks.py src/backend/animetix/creative_tasks.py src/core/domain/services/llm_service.py tests/backend/test_forge.py
git commit -m "feat: inject creative parameters into fusion generation tasks"
```

---

### Task 3: Refactor View and Form Handling

**Files:**
- Modify: `src/backend/animetix/views/forge.py`

- [ ] **Step 1: Write the failing test**

```python
# In tests/backend/test_forge.py
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
def test_archetypist_view_post_creates_fusion_placeholder():
    client = Client()
    # We mock the celery task chain to avoid real execution
    with patch('src.backend.animetix.views.forge.chain') as mock_chain:
        response = client.post(reverse('archetypist'), {
            'title_A': 'Naruto', 'title_B': 'Bleach',
            'media_type_A': 'Anime', 'media_type_B': 'Anime',
            'chaos_level': '80', 'universe_balance': '20', 'art_style': 'Ghibli'
        })
        assert response.status_code == 200
        # Check that tasks were called with the right arguments
        call_args = mock_chain.call_args[0][0].args
        assert call_args[4] == 80 # chaos_level is the 5th arg in signature
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backend/test_forge.py::test_archetypist_view_post_creates_fusion_placeholder -v`
Expected: FAIL

- [ ] **Step 3: Update `forge.py` to handle new inputs and save model**

```python
# In src/backend/animetix/views/forge.py
from ..models import CreativeFusion
# ... existing imports ...

def archetypist_view(request):
    media_type, difficulty, data = get_current_mode(request), request.session.get('difficulty', 'Normal'), animetix_service.load_data(get_current_mode(request))
    if not data: logger.error(f"❌ Archetypist Error: Data for {media_type} not loaded"); return redirect('index')
    cross_options = ArchetypistPresenter.get_cross_media_options(media_type)
    
    if (request.method == 'POST' and request.POST.get('title_A')) or request.GET.get('replay') == '1':
        title_A, title_B = request.POST.get('title_A'), request.POST.get('title_B')
        media_A, media_B = request.POST.get('media_type_A', media_type), request.POST.get('media_type_B', media_type)
        
        # New Parameters
        chaos_level = int(request.POST.get('chaos_level', 50))
        universe_balance = int(request.POST.get('universe_balance', 50))
        art_style = request.POST.get('art_style', 'Cyberpunk')
        parent_id = request.POST.get('parent_id')
        
        data_A, data_B = animetix_service.load_data(media_A) if media_A != media_type else data, animetix_service.load_data(media_B) if media_B != media_type else data
        if not data_A or not data_B: return redirect('index')
        
        valid_A, valid_B = [t for t in data_A.get('titles', []) if t in data_A.get('title_to_full_data', {})], [t for t in data_B.get('titles', []) if t in data_B.get('title_to_full_data', {})]
        if not valid_A or not valid_B: return redirect('index')
        
        t1, t2 = title_A if title_A else random.choice(valid_A[:500]), title_B if title_B else random.choice(valid_B[:500])
        item1, item2 = data_A['title_to_full_data'].get(t1), data_B['title_to_full_data'].get(t2)
        if not item1 or not item2: return redirect('index')
        
        request.session['temp_item_A'], request.session['temp_item_B'] = item1, item2
        
        # Determine parent
        parent_fusion = None
        if parent_id:
            try:
                parent_fusion = CreativeFusion.objects.get(id=parent_id)
            except CreativeFusion.DoesNotExist:
                pass
        
        # Save placeholder fusion (will be updated by a webhook or task result later, or used to track history)
        fusion = CreativeFusion.objects.create(
            title_a=t1, title_b=t2, media_type_a=media_A, media_type_b=media_B,
            chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style,
            creator=request.user if request.user.is_authenticated else None,
            parent=parent_fusion,
            scenario_text="Génération en cours..." # Placeholder
        )
        
        task = chain(
            generate_fusion_scenario_task.s(media_type, item1, item2, request.session.get('language', 'Français'), chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style), 
            generate_fusion_image_task.s(item1, item2, art_style=art_style)
        ).delay()
        
        # We pass fusion.id to the template so it can poll/update it later if needed
        if request.headers.get('HX-Request'): 
            return render(request, 'animetix/archetypist/archetypist_loading_fragment.html', {'task_id': task.id, 'fusion_id': fusion.id})
        return render(request, 'animetix/archetypist/archetypist.html', {'task_id': task.id, 'media_type': media_type, 'item_A': item1, 'item_B': item2, 'show_titles': True, 'fusion_id': fusion.id})
    
    # ... rest of the existing view for GET request ...
    media_settings = DIFFICULTY_SETTINGS.get(media_type, DIFFICULTY_SETTINGS["Anime"])
    # ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/backend/test_forge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/backend/animetix/views/forge.py tests/backend/test_forge.py
git commit -m "feat: update forge view to process creative parameters and save fusion state"
```

---

### Task 4: Frontend UI Refactoring (Cockpit + Background)

**Files:**
- Modify: `src/backend/animetix/templates/animetix/archetypist/archetypist_form.html`

- [ ] **Step 1: Replace form structure with the new Cockpit UI**

Replace the existing `archetypist_form.html` content with a new layout that integrates the sliders and style buttons, while preserving the background `cover-img` loop.

```html
<!-- Replace the central form area in archetypist_form.html with: -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-10 relative z-10">
    <!-- Cockpit (Left Panel) -->
    <div class="lg:col-span-4 space-y-6 text-left">
        <div class="glass-forge-card p-6">
            <h2 class="manga-font text-warning text-sm mb-6 tracking-widest text-center">PARAMÈTRES DE FUSION</h2>
            
            <form id="forge-form" hx-post="{% url 'archetypist' %}" hx-target="#forge-result" hx-indicator="#loading-overlay" hx-swap="innerHTML transition:true">
                {% csrf_token %}
                <input type="hidden" name="parent_id" id="remix-parent-id" value="">
                
                <!-- Alpha / Beta Selectors (Re-use existing JS logic, just style them compactly) -->
                <div class="space-y-4 mb-8">
                    <!-- ALPHA -->
                    <div class="relative">
                        <input type="text" autocomplete="off" name="title_A" id="input-A" 
                               class="w-full bg-white/5 border border-white/10 rounded-xl text-white text-xs py-3 px-4 font-bold" 
                               placeholder="UNIVERS ALPHA" required oninput="searchItems(this, 'results-A', 'preview-A', 'A')">
                        <input type="hidden" name="media_type_A" id="media-type-alpha" value="{{ media_type }}">
                        <div id="results-A" class="search-results-box hidden absolute top-full left-0 w-full z-50"></div>
                    </div>
                    <!-- BETA -->
                    <div class="relative">
                        <input type="text" autocomplete="off" name="title_B" id="input-B" 
                               class="w-full bg-white/5 border border-white/10 rounded-xl text-white text-xs py-3 px-4 font-bold" 
                               placeholder="UNIVERS BÊTA" required oninput="searchItems(this, 'results-B', 'preview-B', 'B')">
                        <input type="hidden" name="media_type_B" id="media-type-beta" value="{{ media_type }}">
                        <div id="results-B" class="search-results-box hidden absolute top-full left-0 w-full z-50"></div>
                    </div>
                </div>

                <!-- Sliders -->
                <div class="space-y-8">
                    <div>
                        <div class="flex justify-between manga-font text-[10px] mb-2 opacity-70">
                            <span class="text-indigo-400">100% ALPHA</span>
                            <span class="text-rose-400">100% BÊTA</span>
                        </div>
                        <input type="range" name="universe_balance" class="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer" value="50" min="0" max="100">
                    </div>

                    <div>
                        <div class="flex justify-between manga-font text-[10px] mb-2 opacity-70">
                            <span>NIVEAU DE CHAOS</span>
                            <span class="text-warning" id="chaos-val">50%</span>
                        </div>
                        <input type="range" name="chaos_level" id="chaos-slider" class="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer" value="50" min="0" max="100" oninput="document.getElementById('chaos-val').innerText = this.value + '%'">
                    </div>

                    <!-- Styles -->
                    <input type="hidden" name="art_style" id="art-style-input" value="Cyberpunk">
                    <div class="grid grid-cols-2 gap-2">
                        <button type="button" onclick="selectStyle(this, 'Cyberpunk')" class="style-btn py-2 px-1 rounded-xl bg-white/5 border border-warning text-[9px] manga-font text-warning">CYBERPUNK</button>
                        <button type="button" onclick="selectStyle(this, 'Ghibli')" class="style-btn py-2 px-1 rounded-xl bg-white/5 border border-white/10 text-[9px] manga-font opacity-50">GHIBLI</button>
                        <button type="button" onclick="selectStyle(this, 'Dark Fantasy')" class="style-btn py-2 px-1 rounded-xl bg-white/5 border border-white/10 text-[9px] manga-font opacity-50">DARK FANTASY</button>
                        <button type="button" onclick="selectStyle(this, 'Retro 8-Bit')" class="style-btn py-2 px-1 rounded-xl bg-white/5 border border-white/10 text-[9px] manga-font opacity-50">8-BIT</button>
                    </div>
                </div>

                <button type="submit" class="btn-forge-active w-full mt-8 text-sm">
                    🔥 FORGER
                </button>
            </form>
        </div>
    </div>

    <!-- Canvas (Right Panel) -->
    <div class="lg:col-span-8">
        <div id="forge-result" class="h-full min-h-[400px]">
            <!-- Default Empty State -->
            <div class="glass-forge-card h-full flex flex-col items-center justify-center p-10 text-center border-dashed border-2 border-white/20">
                <i class="bi bi-magic text-6xl text-white/20 mb-4"></i>
                <p class="manga-font text-white/50 text-xl">LE CANEVAS EST VIDE</p>
                <p class="text-xs text-white/30">Réglez vos paramètres et lancez la forge pour créer une nouvelle réalité.</p>
            </div>
        </div>
    </div>
</div>

<script>
    function selectStyle(btn, styleName) {
        document.getElementById('art-style-input').value = styleName;
        document.querySelectorAll('.style-btn').forEach(b => {
            b.classList.remove('border-warning', 'text-warning', 'opacity-100');
            b.classList.add('border-white/10', 'opacity-50');
        });
        btn.classList.remove('border-white/10', 'opacity-50');
        btn.classList.add('border-warning', 'text-warning', 'opacity-100');
    }
    // Existing searchItems logic remains...
</script>
```

- [ ] **Step 2: Commit**

```bash
git add src/backend/animetix/templates/animetix/archetypist/archetypist_form.html
git commit -m "feat: implement new Cockpit UI for Social Forge"
```

---

### Task 5: Implement Social Actions (Like & Remix Flow)

**Files:**
- Modify: `src/backend/animetix/urls.py`
- Modify: `src/backend/animetix/views/forge.py`
- Modify: `src/backend/animetix/templates/animetix/archetypist/archetypist_result_fragment.html`

- [ ] **Step 1: Create `like_fusion` endpoint**

```python
# In src/backend/animetix/views/forge.py (add at the end)
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def like_fusion(request, fusion_id):
    try:
        fusion = CreativeFusion.objects.get(id=fusion_id)
        if request.user in fusion.likes.all():
            fusion.likes.remove(request.user)
            liked = False
        else:
            fusion.likes.add(request.user)
            liked = True
        
        count = fusion.likes.count()
        icon = "bi-heart-fill text-rose-500" if liked else "bi-heart"
        # Return simple HTML fragment for HTMX to swap the button content
        return HttpResponse(f'<i class="bi {icon} group-hover:scale-125 transition"></i> <span class="manga-font text-xs">{count} LIKES</span>')
    except CreativeFusion.DoesNotExist:
        return HttpResponse("Error", status=404)

# In src/backend/animetix/urls.py (add path)
# path('fusion/<int:fusion_id>/like/', forge.like_fusion, name='like_fusion'),
```

- [ ] **Step 2: Update Result Fragment to include Social Buttons**

```html
<!-- In src/backend/animetix/templates/animetix/archetypist/archetypist_result_fragment.html -->
<!-- Add to the bottom of the result card -->
<div class="grid grid-cols-3 gap-4 mt-6">
    <button hx-post="{% url 'like_fusion' fusion_id %}" hx-swap="innerHTML" class="glass-forge-card py-3 flex items-center justify-center gap-2 hover:bg-rose-500/20 transition group">
        <i class="bi bi-heart"></i>
        <span class="manga-font text-xs">LIKE</span>
    </button>
    <button class="glass-forge-card py-3 flex items-center justify-center gap-2 hover:bg-blue-500/20 transition" onclick="navigator.clipboard.writeText(window.location.href)">
        <i class="bi bi-share text-blue-400"></i>
        <span class="manga-font text-xs">PARTAGER</span>
    </button>
    <button class="bg-white text-black rounded-[20px] manga-font text-xs py-3 hover:scale-105 transition-all" onclick="document.getElementById('remix-parent-id').value='{{ fusion_id }}'; alert('Prêt pour le Remix ! Modifiez les paramètres à gauche.');">
        🔥 REMIXER
    </button>
</div>
```

- [ ] **Step 3: Commit**

```bash
git add src/backend/animetix/views/forge.py src/backend/animetix/urls.py src/backend/animetix/templates/animetix/archetypist/archetypist_result_fragment.html
git commit -m "feat: add like and remix interaction flows"
```
