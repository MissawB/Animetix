import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import StrategyLabPage from '../StrategyLabPage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('../../../components/LazyPlot', () => ({
  default: () => <div>Mocked Plot</div>,
}));

const renderPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <StrategyLabPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('StrategyLabPage', () => {
  it('renders title and run resolution button', () => {
    renderPage();
    // Titre du redesign édition de nuit : "Stratégie de Nash"
    expect(screen.getByRole('heading', { level: 1, name: /Stratégie/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /LANCER LA RÉSOLUTION/i })).toBeInTheDocument();
  });

  it('runs resolution and renders result on success', async () => {
    vi.mocked(apiClient).mockResolvedValue({
      history: [{ iteration: 1, avg_strategy: [0.5], regrets: [0.1] }],
      questions: ['Is character strong?'],
      final_strategy: [0.5],
    });

    renderPage();
    const button = screen.getByRole('button', { name: /LANCER LA RÉSOLUTION/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Convergence de Nash/i)).toBeInTheDocument();
    });
  });
});
