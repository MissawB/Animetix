import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ArchetypeNexusPage from '../ArchetypeNexusPage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ArchetypeNexusPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('ArchetypeNexusPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiClient).mockImplementation(() => new Promise(() => {}));
    renderPage();
    expect(screen.queryByText(/Défaillance Cognitive/i)).not.toBeInTheDocument();
  });

  it('renders error state on fetch failure', async () => {
    vi.mocked(apiClient).mockRejectedValue(new Error('Network error'));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Défaillance Cognitive/i)).toBeInTheDocument();
    });
  });

  it('renders data correctly on successful fetch', async () => {
    vi.mocked(apiClient).mockResolvedValue({
      archetype: {
        id: 'arch_1',
        aura_type: 'Shonen Protagonist',
        intensity: 0.8,
        accent: '#ff0000',
      },
      logical_rules: ['Rule 1'],
      recent_signals: [{ context: 'Signal 1', is_positive: true }],
      cognitive_stats: {
        shonen_affinity: 0.9,
        seinen_affinity: 0.3,
        logic_consistency: 0.8,
        memory_depth: 0.7,
      },
      drift_history: [],
    });

    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Aura: Shonen Protagonist/i)).toBeInTheDocument();
    });
  });
});
