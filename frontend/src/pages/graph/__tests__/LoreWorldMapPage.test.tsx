import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import LoreWorldMapPage from '../LoreWorldMapPage';

vi.mock('../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApiClient = vi.mocked(apiClient);

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <LoreWorldMapPage />
    </QueryClientProvider>,
  );
};

describe('LoreWorldMapPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the communities returned by the API', async () => {
    mockedApiClient.mockResolvedValue([
      { id: 'community_0', name: 'Communauté Anime', summary: 'Un résumé.', entities: ['Naruto'] },
    ]);

    renderPage();

    expect(await screen.findByText('Communauté Anime')).toBeInTheDocument();
  });

  it('shows a generating state instead of crashing when the map is still being built', async () => {
    // The backend answers 202 {"status": "generating"} while the anti-stampede
    // lock is held. apiClient treats 2xx as success, so the page receives an
    // OBJECT where it expects an array — this used to blow up the error boundary
    // with "e?.map is not a function" (prod crash on /fr/graph/map/).
    mockedApiClient.mockResolvedValue({ status: 'generating' });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/cartographie en cours/i)).toBeInTheDocument();
    });
  });

  it('does not crash when the API returns an unexpected shape', async () => {
    mockedApiClient.mockResolvedValue({ unexpected: 'payload' });

    renderPage();

    // No throw: the page falls back to its empty state instead of blowing up.
    await waitFor(() => {
      expect(screen.getByText(/aucune communauté/i)).toBeInTheDocument();
    });
  });
});
