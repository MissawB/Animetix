import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import CommunityFeedPage from '../CommunityFeedPage';
import { fusionService } from '../../../features/social/services/fusionService';
import { CreativeFusion } from '../../../types';

// The page imports a singleton queryClient whose module performs IndexedDB
// persistence on import (unavailable in jsdom). Stub it with a plain client.
vi.mock('../../../utils/queryClient', async () => {
  const { QueryClient } = await import('@tanstack/react-query');
  return { queryClient: new QueryClient() };
});

vi.mock('../../../features/social/services/fusionService', () => ({
  fusionService: {
    getFeed: vi.fn(),
    likeFusion: vi.fn(),
    remixFusion: vi.fn(),
  },
}));

const mockedGetFeed = vi.mocked(fusionService.getFeed);
const mockedLikeFusion = vi.mocked(fusionService.likeFusion);

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <CommunityFeedPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const fusion = (overrides: Partial<CreativeFusion>): CreativeFusion => ({
  id: 1,
  title_a: 'Naruto',
  title_b: 'Bleach',
  media_type_a: 'Anime',
  media_type_b: 'Anime',
  image_url: undefined,
  scenario_text: 'An epic crossover scenario between two shonen worlds.',
  likes_count: 3,
  creator_name: 'Kishimoto',
  is_liked: false,
  ...overrides,
});

describe('CommunityFeedPage', () => {
  beforeEach(() => {
    mockedGetFeed.mockReset();
    mockedLikeFusion.mockReset();
  });

  it('renders the empty state when feed is empty', async () => {
    mockedGetFeed.mockResolvedValue([]);
    renderPage();
    expect(
      await screen.findByText(/Le flux est vide/i)
    ).toBeInTheDocument();
  });

  it('renders populated feed cards', async () => {
    mockedGetFeed.mockResolvedValue([
      fusion({ id: 1, title_a: 'Naruto', title_b: 'Bleach', creator_name: 'Kishimoto' }),
    ]);
    renderPage();
    // Title is rendered as `Naruto × Bleach` (split by a span), so match the
    // standalone creator name and the composed heading text.
    expect(await screen.findByText('Kishimoto')).toBeInTheDocument();
    expect(
      screen.getByText((_content, el) => el?.tagName === 'H3' && /Naruto.*Bleach/.test(el.textContent || ''))
    ).toBeInTheDocument();
  });

  it('triggers like mutation on heart click', async () => {
    mockedGetFeed.mockResolvedValue([fusion({ id: 99 })]);
    mockedLikeFusion.mockResolvedValue({ status: 'ok', likes_count: 4 });
    renderPage();
    const likeCount = await screen.findByText('3');
    const likeButton = likeCount.closest('button') as HTMLButtonElement;
    fireEvent.click(likeButton);
    await waitFor(() => expect(mockedLikeFusion).toHaveBeenCalledWith(99));
  });
});
