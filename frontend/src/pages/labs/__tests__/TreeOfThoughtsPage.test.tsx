import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TreeOfThoughtsPage from '../TreeOfThoughtsPage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('react-force-graph-2d', () => ({
  default: () => <div data-testid="force-graph-mock" />,
}));

const mockedApiClient = vi.mocked(apiClient);

const mockTotData = {
  full_tree: {
    nodes: [
      { id: 'root', type: 'root', score: 1.0, full_text: 'Initial Problem Statement' },
      { id: 'n1', type: 'selected', score: 0.85, full_text: 'Promising Sub-Hypothesis A' },
      { id: 'n2', type: 'pruned', score: 0.2, full_text: 'Impasse Branch B' },
      { id: 'final', type: 'final', score: 0.99, full_text: 'Optimal Deduction' },
    ],
    links: [
      { source: 'root', target: 'n1' },
      { source: 'root', target: 'n2' },
      { source: 'n1', target: 'final' },
    ],
  },
  final_answer: 'Optimal Deduction',
};

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <TreeOfThoughtsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('TreeOfThoughtsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApiClient.mockResolvedValue(mockTotData);
  });

  it('renders sidebar, title, and query input controls', () => {
    renderPage();

    expect(screen.getByText('TREE OF')).toBeInTheDocument();
    expect(screen.getByText('THOUGHTS')).toBeInTheDocument();
    expect(screen.getByLabelText(/Requête cognitive/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: "GÉNÉRER L'ARBRE" })).toBeDisabled();
  });

  it('enables generate button when query is entered and fetches tree', async () => {
    renderPage();

    const textarea = screen.getByLabelText(/Requête cognitive/i);
    fireEvent.change(textarea, { target: { value: 'How to optimize quantum circuit synthesis?' } });

    const generateBtn = screen.getByRole('button', { name: "GÉNÉRER L'ARBRE" });
    expect(generateBtn).toBeEnabled();

    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/labs/tot/', {
        method: 'POST',
        body: JSON.stringify({ query: 'How to optimize quantum circuit synthesis?' }),
      });
    });
  });

  it('displays node legend and reasoning guide sections', () => {
    renderPage();

    expect(screen.getByText(/Légende des Nœuds/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Guide du Raisonnement/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Chemin Sélectionné/i)).toBeInTheDocument();
    expect(screen.getByText(/Branche Élaguée/i)).toBeInTheDocument();
  });
});
