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

  it('maps the communities returned by the API', async () => {
    mockedApiClient.mockResolvedValue([
      { id: 'community_0', name: 'Communauté Anime', summary: 'Un résumé.', entities: ['Naruto'] },
    ]);

    renderPage();

    // The territory is labelled on the plate, and its dossier opens by default.
    expect(await screen.findAllByText('Communauté Anime')).not.toHaveLength(0);
    expect(screen.getByText('Un résumé.')).toBeInTheDocument();
    expect(screen.getByText('Naruto')).toBeInTheDocument();
  });

  it('sizes a territory by its entity count (area encodes weight)', async () => {
    mockedApiClient.mockResolvedValue([
      { id: 'a', name: 'Petit', summary: 's', entities: ['e1'] },
      {
        id: 'b',
        name: 'Grand',
        summary: 's',
        entities: Array.from({ length: 16 }, (_, i) => `e${i}`),
      },
    ]);

    renderPage();

    await screen.findByRole('button', { name: /Grand — 16 entités/i });
    expect(screen.getByRole('button', { name: /Petit — 1 entités/i })).toBeInTheDocument();
  });

  it('shows a survey-in-progress state instead of crashing while the map is built', async () => {
    // The backend answers 202 {"status": "generating"} while the map is being
    // rebuilt. apiClient treats 2xx as success, so the page receives an OBJECT
    // where it expects an array — this used to blow up the error boundary with
    // "e?.map is not a function" (prod crash on /fr/graph/map/).
    mockedApiClient.mockResolvedValue({ status: 'generating' });

    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText(/relevé en cours/i).length).toBeGreaterThan(0);
    });
  });

  it('does not crash when the API returns an unexpected shape', async () => {
    mockedApiClient.mockResolvedValue({ unexpected: 'payload' });

    renderPage();

    // No throw: the plate falls back to its empty state instead of blowing up.
    await waitFor(() => {
      expect(screen.getAllByText(/aucun territoire relevé/i).length).toBeGreaterThan(0);
    });
  });
});
