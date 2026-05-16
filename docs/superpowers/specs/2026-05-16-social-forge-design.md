# Design Spec: The Social Forge (Forge Créative Avancée)

**Date:** 2026-05-16
**Status:** Draft

## 1. Overview
The current "Archetypist" (Creative Forge) feature is a basic utility that takes two universes and generates a combined scenario and image. The goal of this redesign is to transform it into a **community-driven creative ecosystem** called the "Social Forge." It will grant users granular control over the AI generation process and allow them to interact with, like, and "remix" creations made by others.

## 2. Core Objectives
*   **Creative Control:** Introduce sliders for Chaos, Universe Balance, and selectable Artistic Styles.
*   **Social Interaction:** Implement a community feed with upvoting (Likes) and Remix capabilities.
*   **Lineage Tracking:** Ensure every remix tracks its parent, creating a genealogy of creativity.
*   **Aesthetic Continuity:** Maintain the project's signature "Premium Dark Manga" aesthetic, specifically the dynamic floating covers background.

## 3. Data Model (`CreativeFusion`)
A new Django model is required to persist the creations and their metadata.

```python
class CreativeFusion(models.Model):
    # Core Data
    title_a = models.CharField(max_length=255)
    title_b = models.CharField(max_length=255)
    media_type_a = models.CharField(max_length=50)
    media_type_b = models.CharField(max_length=50)
    
    # Generated Assets
    scenario_text = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Creative Parameters (The 'DNA' of the fusion)
    chaos_level = models.IntegerField(default=50) # 0-100
    universe_balance = models.IntegerField(default=50) # 0 (100% A) to 100 (100% B)
    art_style = models.CharField(max_length=100, default='Cyberpunk')
    
    # Social & Lineage
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fusions')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='remixes')
    likes = models.ManyToManyField(User, related_name='liked_fusions', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

## 4. UI/UX Architecture

The `archetypist_form.html` will be heavily refactored while retaining its `cover-img` background animations.

### 4.1. The Control Cockpit (Left Panel)
*   **Universe Selectors:** Existing dual search bars for Alpha and Beta.
*   **Balance Slider:** Ranges from 0 (Alpha) to 100 (Beta). Default 50.
*   **Chaos Meter:** Slider from 0 (Strict logic) to 100 (Abstract/Wild).
*   **Style Presets:** Selectable grid (e.g., Cyberpunk, Ghibli, Dark Fantasy, 8-Bit).

### 4.2. The Canvas (Right/Center Panel)
*   Displays the final generated image.
*   Overlays the scenario text with a cinematic gradient.
*   Displays a "Remix Badge" if the creation has a `parent`.
*   Houses the social action buttons (Like, Share, Download).

### 4.3. The Community Feed (Bottom Section)
*   A masonry or grid layout of recently created or top-liked fusions.
*   Hovering over a card reveals the "🔥 REMIX" button.
*   Clicking Remix populates the Cockpit with the parent's parameters, ready for adjustment.

## 5. Workflow: The Remix Cycle
1.  **Browse:** User sees a fusion in the feed (e.g., *Naruto x Cyberpunk*).
2.  **Trigger:** User clicks "Remix".
3.  **Hydrate:** The cockpit is auto-filled:
    *   Alpha: Naruto
    *   Beta: Cyberpunk
    *   Style: Cyberpunk
    *   Parent ID: [Original Fusion ID] is stored in a hidden input.
4.  **Adjust:** User changes the style to "Ghibli" and increases Chaos.
5.  **Forge:** User clicks "Lancer la Forge". A new generation is triggered.
6.  **Persist:** The new `CreativeFusion` is saved with `parent` pointing to the original.

## 6. API & Backend Services
*   **Tasks Update:** The Celery tasks (`generate_fusion_scenario_task`, `generate_fusion_image_task`) must be updated to accept and utilize the new parameters (`chaos_level`, `balance`, `art_style`) in their LLM/Image Gen prompts.
*   **Social Endpoints:** HTMX endpoints for `like_fusion` and `load_feed`.

## 7. Migration Strategy
1.  Create `CreativeFusion` model and migrate.
2.  Update Celery tasks to accept new prompt modifiers.
3.  Refactor `forge.py` to handle the new form inputs and save the model post-generation.
4.  Implement the UI overhaul in `archetypist_form.html`.
5.  Implement the Community Feed and Remix endpoints.
