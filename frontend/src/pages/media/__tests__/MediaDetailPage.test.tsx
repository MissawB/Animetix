import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';
import MediaDetailPage from '../MediaDetailPage';
import { useMediaDetail } from '../../../features/media/hooks/useMediaDetail';
import { MediaDetail } from '../../../types';

vi.mock('../../../features/media/hooks/useMediaDetail');
vi.mock('../../../features/manga-reader/components/ChapterList', () => ({
  ChapterList: () => <div data-testid="chapter-list">Chapters</div>,
}));

const mockedUseMediaDetail = vi.mocked(useMediaDetail);

type DetailResult = UseQueryResult<MediaDetail, Error>;

const makeResult = (partial: Partial<DetailResult>): DetailResult =>
  ({
    data: undefined,
    isLoading: false,
    isError: false,
    ...partial,
  } as unknown as DetailResult);

const renderAt = (path: string) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/media/:mediaType/:itemId/" element={<MediaDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const media = (overrides: Partial<MediaDetail>): MediaDetail =>
  ({
    id: '1',
    title: 'Cowboy Bebop',
    image: 'http://img/cb.jpg',
    genres: ['Action', 'Sci-Fi'],
    description: 'Space bounty hunters.',
    year: '1998',
    popularity: 5,
    studios: ['Sunrise'],
    author: 'Watanabe',
    micro_tags: ['jazz', 'noir'],
    related_items: [],
    ...overrides,
  } as MediaDetail);

describe('MediaDetailPage', () => {
  beforeEach(() => {
    mockedUseMediaDetail.mockReset();
  });

  it('renders loading state', () => {
    mockedUseMediaDetail.mockReturnValue(makeResult({ isLoading: true }));
    const { container } = renderAt('/media/Anime/1/');
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders not-found state on error', () => {
    mockedUseMediaDetail.mockReturnValue(makeResult({ isError: true }));
    renderAt('/media/Anime/1/');
    expect(screen.getByText(/Œuvre introuvable/i)).toBeInTheDocument();
  });

  it('renders populated anime detail', () => {
    mockedUseMediaDetail.mockReturnValue(makeResult({ data: media({}) }));
    renderAt('/media/Anime/1/');
    expect(screen.getByText('Cowboy Bebop')).toBeInTheDocument();
    expect(screen.getByText('Space bounty hunters.')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Sunrise')).toBeInTheDocument();
    expect(screen.queryByTestId('chapter-list')).not.toBeInTheDocument();
  });

  it('renders manga branch with chapter list and related items', () => {
    mockedUseMediaDetail.mockReturnValue(
      makeResult({
        data: media({
          title: 'Berserk',
          related_items: [
            { id: '2', title: 'Vinland Saga', image: 'http://img/vs.jpg' },
          ],
        }),
      })
    );
    renderAt('/media/manga/1/');
    expect(screen.getByText('Berserk')).toBeInTheDocument();
    expect(screen.getByTestId('chapter-list')).toBeInTheDocument();
    expect(screen.getByText('Vinland Saga')).toBeInTheDocument();
  });
});
