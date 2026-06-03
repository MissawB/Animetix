# XAI Storybook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Storybook story for the `XaiReportViewer` component to enable isolated development and visual testing.

**Architecture:** Use Storybook's `Meta` and `StoryObj` types for type-safe story definition. Provide realistic mock data that conforms to the `XaiReport` API schema.

**Tech Stack:** React, Storybook, TypeScript, Lucide React (via component).

---

### Task 1: Create Storybook Story

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
