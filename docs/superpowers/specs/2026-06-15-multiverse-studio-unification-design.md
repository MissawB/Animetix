# Design Specification: Multiverse Studio Unification

**Topic:** Fusion of Multiverse Lab and Gallery into a unified "Studio / Canvas" interface.
**Date:** 2026-06-15
**Status:** Approved

## 1. Executive Summary
The goal is to unify the current generation (Genesis Forge) and gallery (Nexus Map) workflows of the Multiverse lab into a single, cohesive "Studio / Canvas" experience. The current implementation uses a fixed sidebar for generation and a graph for exploration, with a toggle to switch between views. The new design replaces this with a spatial interaction model where users drag "Genesis Seeds" from a floating toolbox directly onto the Nexus map to trigger lore synthesis.

## 2. Architecture & Components

### 2.1 Component Structure
- **`MultiverseStudioPage`**: The container page.
- **`NexusMap`**: Enhanced version of the current graph area using `react-force-graph-2d`.
- **`GenesisToolbox`**: A floating, draggable panel containing "Seeds" (prompt templates).
- **`UniverseDetailPanel`**: A sliding drawer for inspecting universe details (re-using existing logic).

### 2.2 Data Flow
1. **Drag Start**: User starts dragging a seed from `GenesisToolbox`.
2. **Drop**: User drops the seed on a specific coordinate on the `NexusMap`.
3. **Capture**: `NexusMap` captures the $(x, y)$ coordinates in graph space.
4. **Initiate**: Call the `synthesize` mutation with the seed archetype and the coordinates.
5. **Optimistic Update**: Add a temporary "Latent Node" to the graph state at the drop location.
6. **Conversion**: Once the API returns the generated universe, the Latent Node is updated to a permanent Universe Node.

### 2.3 API Integration
- **GET `/api/v1/multiverse/gallery/`**: Fetches the current graph data.
- **POST `/api/v1/singularity-lab/`**: Triggers lore synthesis (Genesis Forge logic).

## 3. UI/UX Design

### 3.1 Spatial Synthesis
- **Interaction**: Drag and drop replaces the form-based generation.
- **Visuals**: Synthesis nodes show a pulsing effect (Latent State) while processing.
- **Placement**: Dropping a seed near existing universes can (optionally) bias the synthesis towards thematic compatibility.

### 3.2 Floating Toolbox
- **Design**: Sleek, glassmorphic panel.
- **Mobility**: Can be minimized or moved to avoid blocking graph nodes.
- **Content**: Organized by Archetypes (Cyberpunk, Fantasy, etc.).

## 4. Implementation Details

### 4.1 Frontend Changes
- Refactor `MultiverseStudioPage.tsx` to remove the fixed sidebar.
- Implement `GenesisToolbox` component with `framer-motion` for drag/drop.
- Update `ForceGraph2D` to support drop events and render "Latent Nodes".

### 4.2 State Management
- Use `Zustand` or local state to manage the collection of active synthesis processes.
- Ensure `react-query` cache invalidation correctly updates the graph without losing the current viewport/zoom.

## 5. Testing & Validation

### 5.1 Unit Tests
- Test `GenesisToolbox` drag events.
- Test `MultiverseStudioPage` state transitions (Idle -> Synthesizing -> Complete).

### 5.2 E2E Tests (Playwright)
- Verify that dragging a seed onto the map triggers the synthesis API.
- Verify that the resulting universe node appears on the map.

## 6. Self-Review
- **Placeholder scan:** None.
- **Internal consistency:** Architectural plan matches UI mockups.
- **Scope check:** Focused on the unification of the Multiverse page.
- **Ambiguity check:** Interaction model (Drag and Drop) is clearly defined.
