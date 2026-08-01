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
  read_count: 3,
  total_chapters: 5,
  has_started: true,
  created_at: '2026-07-01T00:00:00Z',
  manga: { id: 'm1', title: 'Berserk', author: 'Miura', image: '', media_type: 'Manga' },
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

  // Task 10: the card surfaces server-computed chapter progress and links back
  // to the media detail page (which already renders the "Reprendre" banner),
  // instead of calling the per-manga progress API for every card.
  it('shows the read/total chapter progress and a resume link to the media detail page', async () => {
    mockApiClient.mockResolvedValue([fav]);

    renderPage();

    expect(await screen.findByText('3/5 lus')).toBeInTheDocument();
    const resumeLink = screen.getByRole('link', { name: /reprendre/i });
    expect(resumeLink).toHaveAttribute('href', '/media/Manga/m1/');
  });

  it('hides the resume link when the manga was never opened, or is fully read', async () => {
    mockApiClient.mockResolvedValue([
      { ...fav, id: 2, read_count: 0, total_chapters: 5, has_started: false },
      { ...fav, id: 3, read_count: 5, total_chapters: 5, has_started: true },
    ]);

    renderPage();

    expect(await screen.findByText('0/5 lus')).toBeInTheDocument();
    expect(screen.getByText('5/5 lus')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /reprendre/i })).not.toBeInTheDocument();
  });

  // The card used to key the link on read_count > 0, i.e. "at least one chapter
  // finished". Someone in the middle of chapter 1 has read_count === 0 and got
  // no button, while the media page and the Tachidesk popup were both offering
  // "Reprendre au chapitre 1 — page 12/83" for that very same state.
  it('shows the resume link mid-first-chapter, when no chapter is finished yet', async () => {
    mockApiClient.mockResolvedValue([
      { ...fav, id: 4, read_count: 0, total_chapters: 5, has_started: true },
    ]);

    renderPage();

    expect(await screen.findByText('0/5 lus')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /reprendre/i })).toHaveAttribute(
      'href',
      '/media/Manga/m1/',
    );
  });
});
