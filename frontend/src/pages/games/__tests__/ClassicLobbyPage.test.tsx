import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ClassicLobbyPage from '../ClassicLobbyPage';
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

describe('ClassicLobbyPage', () => {
  beforeEach(() => {
    navigate.mockClear();
    startMock.mockClear();
  });

  it('seeds the classic-state cache with the new game before navigating', async () => {
    const newState = { is_daily: false, guesses: [], game_over: false };
    startMock.mockResolvedValue(newState);

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    // Régression : sans seed du cache après le start, la page de jeu pouvait
    // ré-afficher la partie précédente (ex. le défi du jour) encore « fraîche ».
    qc.setQueryData(CLASSIC_STATE_QUERY_KEY, {
      is_daily: true,
      guesses: [],
      game_over: false,
    });

    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ClassicLobbyPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByText(/Lancer la partie/));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/game/classic/play/'));
    expect(startMock).toHaveBeenCalled();
    expect(qc.getQueryData(CLASSIC_STATE_QUERY_KEY)).toEqual(newState);
  });
});
