import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChapterList } from '../ChapterList';

interface ApiChapter {
  id: number;
  number: number;
  title: string;
  pages: unknown[];
}

interface QueryResult {
  data: ApiChapter[] | undefined;
  isLoading: boolean;
  isError: boolean;
}

interface ChapterProgress {
  number: number;
  is_read: boolean;
  last_page_read: number;
  page_count: number;
}

interface MangaProgressData {
  resume: { chapter_number: number } | null;
  read_count: number;
  total_count: number;
}

let queryResult: QueryResult = { data: undefined, isLoading: true, isError: false };
const invalidateQueriesMock = vi.fn();

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => queryResult,
  useQueryClient: () => ({ invalidateQueries: invalidateQueriesMock }),
}));

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('../ChapterDownloadButton', () => ({
  ChapterDownloadButton: () => <button type="button">download</button>,
}));

// Contrôle réactif de l'auth, comme le vrai store zustand : sélecteur ET
// `.getState()` doivent tous les deux fonctionner sur ce mock.
let mockIsAuthenticated = false;
vi.mock('../../../../store/authStore', () => {
  const state = () => ({ isAuthenticated: mockIsAuthenticated });
  const useAuthStore = Object.assign(
    (selector: (s: { isAuthenticated: boolean }) => unknown) => selector(state()),
    { getState: state },
  );
  return { useAuthStore };
});

// Progression de lecture : mock au niveau du hook (limite de responsabilité de
// ChapterList), fidèle à la vraie signature `(mediaId, enabled)` — quand
// `enabled` est false (visiteur anonyme), aucune donnée n'est renvoyée, comme
// le ferait la vraie query désactivée.
let mockProgressData: MangaProgressData | undefined;
let mockByChapter = new Map<number, ChapterProgress>();
vi.mock('../../progress/useMangaProgress', () => ({
  useMangaProgress: (_mediaId: string, enabled: boolean) =>
    enabled
      ? { data: mockProgressData, byChapter: mockByChapter }
      : { data: undefined, byChapter: new Map() },
  mangaProgressKey: (mediaId: string) => ['manga', mediaId, 'progress'],
}));

const markChaptersReadMock = vi.fn().mockResolvedValue(undefined);
vi.mock('../../progress/progressService', () => ({
  markChaptersRead: (...args: unknown[]) => markChaptersReadMock(...args),
}));

const renderList = () =>
  render(
    <MemoryRouter>
      <ChapterList mediaId="42" mediaTitle="One Piece" />
    </MemoryRouter>,
  );

describe('ChapterList', () => {
  beforeEach(() => {
    queryResult = { data: undefined, isLoading: true, isError: false };
    mockIsAuthenticated = false;
    mockProgressData = undefined;
    mockByChapter = new Map();
    invalidateQueriesMock.mockClear();
    markChaptersReadMock.mockClear();
  });

  it('renders a loading message', () => {
    renderList();
    expect(screen.getByText(/Chargement des chapitres/)).toBeInTheDocument();
  });

  it('renders an error message', () => {
    queryResult = { data: undefined, isLoading: false, isError: true };
    renderList();
    expect(screen.getByText(/Erreur lors du chargement/)).toBeInTheDocument();
  });

  it('renders an empty message when there are no chapters', () => {
    queryResult = { data: [], isLoading: false, isError: false };
    renderList();
    expect(screen.getByText(/Aucun chapitre disponible/)).toBeInTheDocument();
  });

  it('renders chapter rows with titles and links', () => {
    queryResult = {
      isLoading: false,
      isError: false,
      data: [
        { id: 1, number: 1, title: 'Romance Dawn', pages: [] },
        { id: 2, number: 2, title: '', pages: [] },
      ],
    };
    renderList();
    expect(screen.getByText('Romance Dawn')).toBeInTheDocument();
    // Falls back to "Chapitre {number}" when no title is provided.
    expect(screen.getByText('Chapitre 2')).toBeInTheDocument();
    expect(screen.getByText('Romance Dawn').closest('a')).toHaveAttribute(
      'href',
      '/media/manga/42/1/',
    );
  });

  it('shows the resume banner and read badges for an authenticated visitor', () => {
    mockIsAuthenticated = true;
    mockProgressData = { resume: { chapter_number: 2 }, read_count: 1, total_count: 2 };
    mockByChapter = new Map([
      [1, { number: 1, is_read: true, last_page_read: 82, page_count: 83 }],
    ]);
    queryResult = {
      isLoading: false,
      isError: false,
      data: [
        { id: 1, number: 1, title: 'Romance Dawn', pages: [] },
        { id: 2, number: 2, title: 'Buggy the Clown', pages: [] },
      ],
    };
    renderList();

    // Bandeau de reprise, avec les bons compteurs.
    expect(screen.getByText(/Reprendre au chapitre 2/i)).toBeInTheDocument();
    expect(screen.getByText('1/2 lus')).toBeInTheDocument();

    // Chapitre 1 : progression connue et lue -> badge "lu".
    expect(screen.getByRole('button', { name: /marquer comme non lu/i })).toBeInTheDocument();
    // Chapitre 2 : pas d'entrée dans byChapter -> badge par défaut "non lu".
    expect(screen.getByRole('button', { name: /marquer comme lu/i })).toBeInTheDocument();
  });

  it('toggles read state via markChaptersRead and invalidates the progress cache', async () => {
    mockIsAuthenticated = true;
    mockProgressData = { resume: null, read_count: 0, total_count: 1 };
    mockByChapter = new Map([
      [1, { number: 1, is_read: true, last_page_read: 82, page_count: 83 }],
    ]);
    queryResult = {
      isLoading: false,
      isError: false,
      data: [{ id: 1, number: 1, title: 'Romance Dawn', pages: [] }],
    };
    renderList();

    const toggleBtn = screen.getByRole('button', { name: /marquer comme non lu/i });
    await userEvent.click(toggleBtn);

    expect(markChaptersReadMock).toHaveBeenCalledWith('42', [1], false);
    await waitFor(() =>
      expect(invalidateQueriesMock).toHaveBeenCalledWith({
        queryKey: ['manga', '42', 'progress'],
      }),
    );
  });

  it('renders no resume banner and no read badges for an anonymous visitor', () => {
    mockIsAuthenticated = false;
    // Même si des données de progression existaient quelque part, un visiteur
    // anonyme ne doit jamais les voir ni déclencher le hook en mode "enabled".
    mockProgressData = { resume: { chapter_number: 2 }, read_count: 1, total_count: 2 };
    mockByChapter = new Map([
      [1, { number: 1, is_read: true, last_page_read: 82, page_count: 83 }],
    ]);
    queryResult = {
      isLoading: false,
      isError: false,
      data: [
        { id: 1, number: 1, title: 'Romance Dawn', pages: [] },
        { id: 2, number: 2, title: 'Buggy the Clown', pages: [] },
      ],
    };
    renderList();

    expect(screen.queryByText(/Reprendre au chapitre/i)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /marquer comme (non )?lu/i }),
    ).not.toBeInTheDocument();
  });
});
