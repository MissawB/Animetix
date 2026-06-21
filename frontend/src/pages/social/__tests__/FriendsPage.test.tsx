import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import FriendsPage from '../FriendsPage';
import { useSocialDashboard } from '../../../features/social/hooks/useSocialDashboard';
import { Friendship, SocialDashboardData } from '../../../types';

vi.mock('../../../features/social/hooks/useSocialDashboard');

const mockedUseSocialDashboard = vi.mocked(useSocialDashboard);

interface DashboardHook {
  data: SocialDashboardData | undefined;
  isLoading: boolean;
  isError: boolean;
  toggleFollow: (userId: number) => void;
}

const toggleFollow = vi.fn();

const makeHook = (partial: Partial<DashboardHook>): DashboardHook => ({
  data: undefined,
  isLoading: false,
  isError: false,
  toggleFollow,
  ...partial,
});

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <FriendsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const friend = (overrides: Partial<Friendship>): Friendship => ({
  id: 1,
  to_user: 42,
  username: 'naruto',
  level: 9,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

describe('FriendsPage', () => {
  beforeEach(() => {
    mockedUseSocialDashboard.mockReset();
    toggleFollow.mockReset();
  });

  it('renders loading state', () => {
    mockedUseSocialDashboard.mockReturnValue(makeHook({ isLoading: true }));
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders error state', () => {
    mockedUseSocialDashboard.mockReturnValue(makeHook({ isError: true }));
    renderPage();
    expect(screen.getByText('common.error')).toBeInTheDocument();
  });

  it('renders empty network placeholders when no friends', () => {
    mockedUseSocialDashboard.mockReturnValue(
      makeHook({ data: { following: [], followers: [] } })
    );
    renderPage();
    expect(
      screen.getByText(/Vous ne suivez personne pour l'instant/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Pas encore d'abonnés/i)).toBeInTheDocument();
  });

  it('renders populated following and followers and unfollows', () => {
    mockedUseSocialDashboard.mockReturnValue(
      makeHook({
        data: {
          following: [friend({ id: 1, to_user: 7, username: 'sasuke' })],
          followers: [friend({ id: 2, to_user: 8, username: 'sakura' })],
        },
      })
    );
    renderPage();
    expect(screen.getByText('sasuke')).toBeInTheDocument();
    expect(screen.getByText('sakura')).toBeInTheDocument();

    fireEvent.click(screen.getByText(/Unfollow/i));
    expect(toggleFollow).toHaveBeenCalledWith(7);
  });
});
