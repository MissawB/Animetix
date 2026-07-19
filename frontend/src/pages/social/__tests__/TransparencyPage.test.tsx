import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TransparencyPage from '../TransparencyPage';

// Fixture with a single timeline point so the evolution section renders its
// "not enough data" fallback rather than the Plotly chart — keeps the test out
// of plotly.js / jsdom canvas territory while still exercising the section.
const MOCK_DATA = {
  global_metrics: {
    total_feedbacks: 12345,
    knowledge_nodes: 6789,
    community_satisfaction: 0.92,
    model_version: 'Champion v2.4',
    last_training: '2026-07-01',
  },
  evolution_timeline: [{ date: '2026-06', accuracy: 0.85 }],
  sota_benchmarks: [],
  embedding_drift: {
    genre_embeddings: { status: 'healthy', p_value: 0.42, sample_size: 500 },
  },
  ethics_score: 98,
  model_uptime: 99,
  ethics_audit: { safety_compliance: 0.995, hallucination_rate: 0.012 },
};

const renderPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TransparencyPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('TransparencyPage', () => {
  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(MOCK_DATA) }),
    ) as unknown as typeof fetch;
  });

  it('renders the hero, KPIs, model comparison, drift audit, ethics and CTA sections', async () => {
    renderPage();

    // Hero
    expect(await screen.findByText(/transparence/i)).toBeInTheDocument();
    // KPI — model version from global_metrics
    expect(screen.getByText('Champion v2.4')).toBeInTheDocument();
    // KPI — satisfaction (0.92 * 100)
    expect(screen.getByText('92%')).toBeInTheDocument();
    // Model comparison card title = model_id.split('/').pop()
    expect(screen.getByText('Qwen3.5-9B')).toBeInTheDocument();
    // Drift audit key
    expect(screen.getByText('genre_embeddings')).toBeInTheDocument();
    // Ethics commitments + security audit sections
    expect(screen.getByText(/ENGAGEMENTS ÉTHIQUES/i)).toBeInTheDocument();
    expect(screen.getByText(/Audit de Sécurité/i)).toBeInTheDocument();
    // Evolution section fallback (single timeline point)
    expect(screen.getByText(/Pas encore assez de données/i)).toBeInTheDocument();
    // Participation CTA
    expect(screen.getByText(/Devenez Curateur du Nexus/i)).toBeInTheDocument();
  });

  it('shows the loading state before data resolves', () => {
    renderPage();
    expect(screen.getByText(/Synchronisation avec le Nexus/i)).toBeInTheDocument();
  });
});
