# Multiverse Studio Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify generation and gallery workflows into a single "Studio / Canvas" interaction model with spatial synthesis.

**Architecture:** Refactor `MultiverseStudioPage` to use a central `NexusMap` (Force Graph) and a floating `GenesisToolbox`. Implement drag-and-drop synthesis.

**Tech Stack:** React 19, Framer Motion, Lucide React, react-force-graph-2d, Django (DRF).

---

### Task 1: Backend - Multiverse Synthesis Endpoint

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Test: `tests/pipeline/test_singularity.py` (Existing, verify coverage)

- [ ] **Step 1: Verify missing synthesis action**
Check `SingularityLabDataView.post` in `backend/api/animetix/api/labs.py`.

- [ ] **Step 2: Implement 'synthesize' action**
Modify `SingularityLabDataView.post` to handle `action == 'synthesize'`.

```python
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
```

- [ ] **Step 3: Test with manual API call**
Run: `pytest tests/pipeline/test_singularity.py`
Expected: PASS

---

### Task 2: Frontend - GenesisToolbox Component

**Files:**
- Create: `frontend/src/features/labs/components/Multiverse/GenesisToolbox.tsx`
- Create: `frontend/src/features/labs/components/Multiverse/__tests__/GenesisToolbox.test.tsx`

- [ ] **Step 1: Write GenesisToolbox component**
Create `GenesisToolbox.tsx` with floating/draggable behavior using `framer-motion`.

```tsx
import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Shield, Wand2 } from 'lucide-react';

const SEEDS = [
  { id: 'Cyberpunk', label: 'Cyberpunk', icon: Zap, color: '#06b6d4' },
  { id: 'Fantasy', label: 'Fantasy', icon: Sparkles, color: '#a855f7' },
  { id: 'Sci-Fi', label: 'Sci-Fi', icon: Wand2, color: '#10b981' },
  { id: 'Steampunk', label: 'Steampunk', icon: Shield, color: '#f59e0b' },
];

interface GenesisToolboxProps {
  onDragStart: (seed: string) => void;
}

export const GenesisToolbox: React.FC<GenesisToolboxProps> = ({ onDragStart }) => {
  return (
    <motion.div 
      drag
      dragMomentum={false}
      className="absolute top-8 left-8 w-64 bg-black/60 backdrop-blur-2xl border border-white/10 rounded-3xl p-6 z-50 shadow-2xl"
    >
      <header className="mb-6 border-b border-white/5 pb-4">
        <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-red-500">Genesis Seeds</h3>
      </header>
      <div className="space-y-3">
        {SEEDS.map((seed) => (
          <div 
            key={seed.id}
            draggable
            onDragStart={() => onDragStart(seed.id)}
            className="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-all cursor-grab active:cursor-grabbing group"
          >
            <seed.icon className="w-5 h-5" style={{ color: seed.color }} />
            <span className="text-xs font-black uppercase text-white/70 group-hover:text-white">{seed.label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
```

- [ ] **Step 2: Write test for GenesisToolbox**
Expected: Component renders and handles drag start.

---

### Task 3: Frontend - NexusMap Component

**Files:**
- Create: `frontend/src/features/labs/components/Multiverse/NexusMap.tsx`

- [ ] **Step 1: Implement NexusMap with drop support**
Create `NexusMap.tsx` wrapping `ForceGraph2D`.

```tsx
import React, { useRef, useCallback } from 'react';
import _ForceGraph2D from 'react-force-graph-2d';
const ForceGraph2D = (_ForceGraph2D as any).default || _ForceGraph2D;

interface NexusMapProps {
  data: any;
  loadingNodes: any[];
  onDropSeed: (seed: string, x: number, y: number) => void;
  onNodeClick: (node: any) => void;
}

export const NexusMap: React.FC<NexusMapProps> = ({ data, loadingNodes, onDropSeed, onNodeClick }) => {
  const fgRef = useRef<any>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const seed = e.dataTransfer.getData('seed');
    if (!fgRef.current) return;
    
    // Transform client coordinates to graph coordinates
    const { x, y } = fgRef.current.screen2GraphCoords(e.clientX, e.clientY);
    onDropSeed(seed, x, y);
  }, [onDropSeed]);

  return (
    <div 
      className="w-full h-full relative bg-[#05050a]" 
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        nodeLabel="name"
        onNodeClick={onNodeClick}
        // Custom rendering for latent nodes
        nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
           // Reuse existing nodeCanvasObject logic but add pulsing for loadingNodes
        }}
      />
    </div>
  );
};
```

---

### Task 4: Frontend - Final Integration in MultiverseStudioPage

**Files:**
- Modify: `frontend/src/pages/labs/MultiverseStudioPage.tsx`

- [ ] **Step 1: Refactor Page logic**
Integrate `GenesisToolbox` and `NexusMap`. Remove old sidebar.

- [ ] **Step 2: Orchestrate Synthesis State**
Add local state for `activeSynthesis` (latent nodes). Update `onDropSeed` to mutate and add latent node.

- [ ] **Step 3: Verification**
E2E check: Drag seed -> Synthesis starts -> Pulsing node appears -> Universe appears.
