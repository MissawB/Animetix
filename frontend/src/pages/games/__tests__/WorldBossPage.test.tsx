import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import WorldBossPage from '../WorldBossPage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApi = vi.mocked(apiClient);

const BOSS = {
  id: 3,
  title: 'RAID OMEGA · S28',
  media_type: 'Anime',
  total_hp: 100000,
  current_hp: 74000,
  community_hints: [],
  is_active: true,
  reward_xp: 1000,
  current_phase: 2,
};
const QUESTION = {
  tier: 1,
  band: 'A',
  timer: 20,
  damage: 1,
  limiter_break: false,
  streak: 0,
  run_damage: 0,
  best_tier: 0,
  archetype: 'year',
  prompt: 'En quelle année ?',
  options: ['1996', '1998', '2001', '2004'],
  image: null,
};

const route = (url: string) => {
  if (url.includes('/active/')) return Promise.resolve(BOSS);
  if (url.includes('/leaderboard/')) return Promise.resolve({ boss_id: 3, leaderboard: [] });
  if (url.includes('/question/')) return Promise.resolve(QUESTION);
  return Promise.resolve({});
};

const renderPage = () =>
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <WorldBossPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe('WorldBossPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.mockImplementation((url: string) => route(url));
  });

  it('shows the collective health bar and the ladder', async () => {
    renderPage();

    expect(await screen.findByText(/74\s?000/)).toBeInTheDocument();
    expect(screen.getByText(/échelle de puissance/i)).toBeInTheDocument();
    expect(screen.getByText('2048')).toBeInTheDocument();
  });

  it('asks a question and reveals the answer once picked', async () => {
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: /commencer la montée/i }));
    expect(await screen.findByText('En quelle année ?')).toBeInTheDocument();

    mockedApi.mockResolvedValueOnce({
      correct: true,
      late: false,
      damage_dealt: 1,
      correct_index: 1,
      correct_label: '1998',
      subject: 'Cowboy Bebop',
      tier: 2,
      run_damage: 1,
      best_tier: 1,
      limiter_break: false,
      streak: 0,
      boss: { current_hp: 73999, total_hp: 100000, current_phase: 2, is_active: true },
    });
    await userEvent.click(screen.getByRole('button', { name: '1998' }));

    expect(await screen.findByText(/\+1 dégâts/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /question suivante/i })).toBeInTheDocument();
  });

  it('survives a boss that does not exist', async () => {
    mockedApi.mockRejectedValue(new Error('404'));
    renderPage();
    expect(await screen.findByText(/aucun boss actif/i)).toBeInTheDocument();
  });

  it('survives a payload that is not the shape it expects', async () => {
    mockedApi.mockImplementation((url: string) =>
      url.includes('/leaderboard/') ? Promise.resolve({ leaderboard: 'nope' }) : route(url),
    );
    renderPage();
    await waitFor(() => expect(screen.getByText(/raid omega/i)).toBeInTheDocument());
  });
});
