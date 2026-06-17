import type { Meta, StoryObj } from '@storybook/react-vite';
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
