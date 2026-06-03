# XAI Report Viewer Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable, modern React widget to display the Hybrid XAI Report (Agent Trace, LLM Diagnostics, RAG Attribution).

**Architecture:** A standalone React component that takes a `XaiReport` object (generated from our OpenAPI schema) as props. It uses Tailwind CSS for styling (dark card widget aesthetic) and `lucide-react` for icons. 

**Tech Stack:** React 19, TypeScript, Tailwind CSS, Lucide React.

---

### Task 1: Create XaiReportViewer Component

**Files:**
- Create: `frontend/src/components/xai/XaiReportViewer.tsx`

- [ ] **Step 1: Write the basic component structure with types**

```tsx
import React from 'react';
import { BrainCircuit, CheckCircle2, ChevronRight, BookOpen, Fingerprint } from 'lucide-react';
import type { components } from '../../types/api';

type XaiReport = components['schemas']['XaiReport'];

export interface XaiReportViewerProps {
  report: XaiReport;
  className?: string;
}

export const XaiReportViewer: React.FC<XaiReportViewerProps> = ({ report, className = '' }) => {
  return (
    <div className={`font-sans bg-slate-900 text-slate-50 w-full max-w-2xl rounded-xl shadow-lg border border-slate-700 overflow-hidden ${className}`}>
      {/* Component content goes here */}
    </div>
  );
};
```

- [ ] **Step 2: Implement the Header (Intent & Confidence)**
Add the header section showing the `query_intent` and `final_confidence`. Format the confidence as a percentage.

- [ ] **Step 3: Implement the Agent Trace (Timeline)**
Map over `report.agent_trace` to display a vertical timeline of the agents' thoughts. Use simple CSS borders for the timeline connecting line.

- [ ] **Step 4: Implement Data Grid (Attribution & Tokens)**
Create a two-column grid. 
Left column: Map over `report.retrieval_attribution` to show progress bars for `contribution_weight` (or `relevance_score`).
Right column: Map over `report.internal_diagnostics?.top_influential_tokens` to show token pills.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/xai/XaiReportViewer.tsx
git commit -m "feat(frontend): create XaiReportViewer widget component"
```

### Task 2: Create Storybook Story

**Files:**
- Create: `frontend/src/components/xai/XaiReportViewer.stories.tsx`

- [ ] **Step 1: Write the Storybook setup and mock data**

```tsx
import type { Meta, StoryObj } from '@storybook/react';
import { XaiReportViewer } from './XaiReportViewer';

const meta = {
  title: 'XAI/XaiReportViewer',
  component: XaiReportViewer,
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof XaiReportViewer>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockReport = {
  query_intent: "Expliquer le Nen",
  final_confidence: 0.85,
  uncertainty: { method: "gpt2_proxy", is_reliable: true },
  agent_trace: [
    { agent: "Planner", thought: "Recherche d'informations basiques." },
    { agent: "Searcher", thought: "Extraction de Wiki Nen." },
    { agent: "Synthesizer", thought: "Rédaction en cours..." }
  ],
  retrieval_attribution: [
    { document_id: "1", title: "Wiki Nen", relevance_score: 0.95, contribution_weight: 1.0 }
  ],
  internal_diagnostics: {
    attention_heatmap: [],
    top_influential_tokens: ["Nen", "Aura", "Hunter"],
    logit_lens_trajectory: []
  }
};

export const Default: Story = {
  args: {
    report: mockReport,
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/xai/XaiReportViewer.stories.tsx
git commit -m "test(frontend): add storybook for XaiReportViewer"
```