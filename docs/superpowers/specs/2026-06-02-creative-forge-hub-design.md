# Design Spec: Creative Forge Hub (Forge des Mondes)

**Date:** 2026-06-02
**Status:** Approved
**Topic:** Centralizing all media labs and creation tools into a unified, immersive portal.

---

## 1. Overview

The **Creative Forge Hub** (internally "Forge des Mondes") is the new central nerve center for creation within Animetix. It replaces the fragmented access to various "Labs" and the original "Forge" with a single, highly visual, and atmospheric entry point.

### Success Criteria
- [ ] Users can access all creative tools from a single page.
- [ ] Media types are logically categorized (Narrative, Visual, Audio, Experimental).
- [ ] The interface maintains the "Omega Level" aesthetic of Animetix.
- [ ] Navigation is fluid and immersive (animations, glows, high-quality icons).

---

## 2. Architecture & Categorization

The Hub will be organized into four main pillars, each represented by a symbolic relic:

### A. Narratif (Narrative) - Amber Glow
- **Symbol:** Ancient/Futuristic Book.
- **Primary Tool:** The Forge (Scenario & Universe Fusion).
- **Secondary Tools:** Storytelling assistants, Lore generators.

### B. Visuel (Visual) - Blue Glow
- **Symbol:** Painting Frame / Holographic Display.
- **Tools:** Manga Lab, Video Lab, Visual Nexus, Cinematic Reconstruction, Spatial Lab.

### C. Audio (Audio) - Emerald Glow
- **Symbol:** Advanced Headphones.
- **Tools:** Audio Lab, Soundscape Lab, Speech-to-Speech Lab.

### D. Expérimental (Experimental) - Red Glow
- **Symbol:** Alchemical Flask.
- **Tools:** Singularity Lab (Quantum Cognition, Swarm Intelligence, Synaptic Plasticity, JIT Optimizer, Multiverse Genesis).

---

## 3. UI/UX Design

### Visual Layout
- **Background:** Deep black (`#020202`) with subtle red/blue ambient glows and particle effects.
- **Navigation:** Horizontal layout of four large interactive items.
- **Typography:** `Orbitron` for titles (Manga-font), `Inter` for descriptions.

### Interactive States
- **Hover:** The targeted relic scales up, its specific glow intensifies, and a secondary label/description appears.
- **Click (Focus):** The selected category takes focus, pushing others aside or transitioning to a dedicated "Category View" listing the specific lab modules.

### Tech Stack
- **Frontend:** React 19, Tailwind CSS.
- **Animations:** Framer Motion (Transitions and floating effects).
- **Icons:** Custom SVGs (as seen in mockup) or stylized Lucide icons.

---

## 4. Implementation Details

### Routing
- The Hub will be accessible via `/forge-hub/` (replaces or maps from `/forge/` and `/lab/`).
- Category sub-routes (e.g., `/forge-hub/visual/`) will show the specific list of labs.

### Localization
- Full support for French and English via `i18next`.
- Key labels: "Forge des Mondes", "Narratif", "Visuel", "Audio", "Experimental".

---

## 5. Security & Performance
- **Lazy Loading:** Each lab module remains lazy-loaded to keep the Hub performance high.
- **Access Control:** "Omega Level" badges for experimental labs to signify high-complexity/beta status.

---

## 6. Self-Review Notes
- **Placeholder scan:** No TBDs. Routes are defined based on existing `LabRoutes.tsx`.
- **Consistency:** Matches the hexagonal architecture of the backend by acting as a clean Presentation layer.
- **Scope:** Focused on the Hub UI and routing reorganization.
