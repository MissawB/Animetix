import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import DailyChallengePage from '../DailyChallengePage';
import { CLASSIC_STATE_QUERY_KEY } from '../../../features/games/hooks/useClassicGame';

const navigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => navigate };
});

const startMock = vi.fn();
vi.mock('../../../features/games/services/classicService', () => ({
  classicGameService: { start: (...args: unknown[]) => startMock(...args) },
}));

vi.mock('../../../features/utils/hooks/useDailyChallenge', () => ({
  useDailyChallenge: () => ({
    data: {
      date: '2026-07-04',
      is_today: true,
      prev_date: null,
      next_date: null,
      total_score: 0,
      modes: [
        {
          id: 'anime',
          brush1: 'ANIME',
          brush2: 'DU JOUR',
          gradient: 'from-blue-500 to-purple-500',
          description: 'desc',
          icon: '/icon.png',
          media_type: 'Anime',
          completed: false,
          score: null,
        },
      ],
    },
    isLoading: false,
    isError: false,
  }),
}));

describe('DailyChallengePage', () => {
  beforeEach(() => {
    navigate.mockClear();
    startMock.mockClear();
  });

  it('seeds the classic-state cache with the daily game before navigating', async () => {
    const dailyState = { is_daily: true, guesses: [], game_over: false };
    startMock.mockResolvedValue(dailyState);

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    // Régression : une partie classique « fraîche » traîne en cache (staleTime
    // global 5 min, persisté). Sans seed explicite après le start du daily, la
    // page de jeu ré-affichait cette ancienne partie au lieu du défi du jour.
    qc.setQueryData(CLASSIC_STATE_QUERY_KEY, {
      is_daily: false,
      guesses: [],
      game_over: false,
    });

    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <DailyChallengePage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByText('ANIME'));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/game/classic/play/'));
    expect(startMock).toHaveBeenCalledWith('Anime', 'Normal', undefined, true, '2026-07-04');
    expect(qc.getQueryData(CLASSIC_STATE_QUERY_KEY)).toEqual(dailyState);
  });
});
