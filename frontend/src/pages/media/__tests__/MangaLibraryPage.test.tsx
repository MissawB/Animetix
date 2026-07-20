import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MangaLibraryPage from '../MangaLibraryPage';

const mockApiClient = vi.fn();
vi.mock('../../../utils/apiClient', () => ({
  apiClient: (...args: unknown[]) => mockApiClient(...args),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MangaLibraryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const fav = {
  id: 1,
  status: 'reading',
  last_read_chapter: 3,
  unread_chapters_count: 2,
  created_at: '2026-07-01T00:00:00Z',
  manga: { id: 'm1', title: 'Berserk', author: 'Miura', image: '' },
};

describe('MangaLibraryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Audit dette 2026-07-19: a failed load used to be swallowed and rendered as
  // an (empty) library — misleading. It must now surface a distinct error state.
  it('shows an error state (not the empty state) when the favorites query fails', async () => {
    mockApiClient.mockRejectedValue(new Error('401 Unauthorized'));

    renderPage();

    expect(await screen.findByText(/Bibliothèque indisponible/i)).toBeInTheDocument();
    expect(screen.getByText(/Réessayer/i)).toBeInTheDocument();
    // The "empty library" copy must NOT be shown on a load failure.
    expect(screen.queryByText(/Bibliothèque vide/i)).not.toBeInTheDocument();
  });

  it('renders the empty state when the query succeeds with no favorites', async () => {
    mockApiClient.mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/Bibliothèque vide/i)).toBeInTheDocument();
    expect(screen.queryByText(/Bibliothèque indisponible/i)).not.toBeInTheDocument();
  });

  it('renders favorites when the query returns data', async () => {
    mockApiClient.mockResolvedValue([fav]);

    renderPage();

    expect(await screen.findByText('Berserk')).toBeInTheDocument();
  });
});
