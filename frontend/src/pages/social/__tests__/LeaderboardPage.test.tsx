import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';
import LeaderboardPage from '../LeaderboardPage';
import { useLeaderboard } from '../../../features/social/hooks/useLeaderboard';
import { Profile } from '../../../types';

vi.mock('../../../features/social/hooks/useLeaderboard');

const mockedUseLeaderboard = vi.mocked(useLeaderboard);

type LeaderboardResult = UseQueryResult<Profile[], Error>;

const makeResult = (partial: Partial<LeaderboardResult>): LeaderboardResult =>
  ({
    data: undefined,
    isLoading: false,
    isError: false,
    ...partial,
  } as unknown as LeaderboardResult);

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <LeaderboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('LeaderboardPage', () => {
  beforeEach(() => {
    mockedUseLeaderboard.mockReset();
  });

  it('renders loading skeleton state', () => {
    mockedUseLeaderboard.mockReturnValue(makeResult({ isLoading: true }));
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders error state', () => {
    mockedUseLeaderboard.mockReturnValue(makeResult({ isError: true }));
    renderPage();
    expect(screen.getByText('common.error')).toBeInTheDocument();
  });

  it('renders populated leaderboard with players and ranks', () => {
    const players: Profile[] = [
      { username: 'alice', xp: 5000, level: 12 },
      { username: 'bob', xp: 4000, level: 10 },
      { username: 'carol', xp: 3000, level: 8 },
    ];
    mockedUseLeaderboard.mockReturnValue(makeResult({ data: players }));
    renderPage();
    expect(screen.getByText('social.leaderboard.title')).toBeInTheDocument();
    expect(screen.getByText('alice')).toBeInTheDocument();
    expect(screen.getByText('bob')).toBeInTheDocument();
    expect(screen.getByText('carol')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('5000 XP')).toBeInTheDocument();
  });

  it('treats non-array data as empty list', () => {
    mockedUseLeaderboard.mockReturnValue(makeResult({ data: undefined }));
    renderPage();
    expect(screen.getByText('social.leaderboard.title')).toBeInTheDocument();
  });
});
