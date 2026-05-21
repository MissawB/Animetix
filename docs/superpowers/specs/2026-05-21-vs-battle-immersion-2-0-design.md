# Design Spec: VS Battle Game Engine (Immersion 2.0)

## 1. Overview
Upgrade to the VS Battle game mode focusing on visual immersion and real-time feedback. Includes character images, visual power gauges, and a streaming debate effect.

## 2. New Features

### A. Image Extraction
- **Adapter Upgrade:** `FandomAdapter` will now extract the main image URL from the character's infobox.
- **Entity Update:** `CombatCharacter` schema will include an `image_url: str` field.

### B. Visual Power Gauges
- **Logic:** `VsBattleService` will map VS Battles Wiki Tiers (e.g., 10-C to 0) to a numeric scale (0-100) for UI rendering.
- **Scale Example:**
    - Tier 10 (Human): 0-10%
    - Tier 4 (Solar System): 50-60%
    - Tier 1 (Extra-dimensional): 90-100%
- **Display:** Horizontal animated progress bars on character cards.

### C. Real-time Streaming (Typewriter Effect)
- **Frontend Logic:** Use JavaScript to render the `debate_history` with a typewriter effect.
- **UI:** A dedicated terminal-style container with a blinking cursor.

## 3. Architecture Changes

### Domain Layer (Core)
- **Entities:**
    - `CombatStats` adds `tier_value: int` (normalized scale).
    - `CombatCharacter` adds `image_url: Optional[str]`.
- **Service:** `VsBattleService` implements the `tier_to_value` mapping logic.

### Adapter Layer
- **FandomAdapter:** Uses MediaWiki `prop=pageimages` or `prop=images` to find the primary character portrait.

## 4. UI/UX Refinement
- **Theme:** "Deep Space / Arena" (Black/Gold/Red).
- **Responsiveness:** Grid layout for side-by-side comparison on desktop, vertical stack on mobile.

## 5. Testing
- Verify image URL extraction with various wiki page formats.
- Validate the normalization logic for edge-case tiers (e.g., "Unknown", "Variable").
