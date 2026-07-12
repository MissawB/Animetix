import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import WorldBossPage, { buildQuestionId } from '../WorldBossPage';
import { apiClient } from '../../../utils/apiClient';
import { useAuthStore } from '../../../store/authStore';

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
    // Frapper le boss exige d'être connecté (le serveur le sait, la page aussi
    // désormais) : sauf mention contraire, ces tests jouent un joueur connecté.
    useAuthStore.setState({ isAuthenticated: true });
  });

  it('refuses to start the climb for a visitor who is not logged in', async () => {
    // Cliquable hors connexion, le bouton ne produisait qu'un toast 401 : le jeu
    // proposait une action qui ne pouvait que rater.
    useAuthStore.setState({ isAuthenticated: false });
    renderPage();

    const start = await screen.findByRole('button', { name: /commencer la montée/i });
    expect(start).toBeDisabled();
    expect(screen.getByText(/connecte-toi pour frapper le boss/i)).toBeInTheDocument();

    await userEvent.click(start);
    expect(mockedApi).not.toHaveBeenCalledWith(
      expect.stringContaining('/question/'),
      expect.anything(),
    );
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

  it('survives a boss payload missing its HP fields', async () => {
    // Only the percentage division guarded against a missing total_hp — the
    // current/total display called .toLocaleString() unconditionally and
    // threw on a payload that never had current_hp/total_hp in the first
    // place (not just falsy ones).
    const BOSS_NO_HP = {
      id: 3,
      title: 'RAID OMEGA · S28',
      media_type: 'Anime',
      community_hints: [],
      is_active: true,
      reward_xp: 1000,
      current_phase: 2,
    };
    mockedApi.mockImplementation((url: string) =>
      url.includes('/active/') ? Promise.resolve(BOSS_NO_HP) : route(url),
    );
    renderPage();
    expect(await screen.findByText(/raid omega/i)).toBeInTheDocument();
  });

  it('disables the options while the answer is in flight, before the verdict returns', async () => {
    renderPage();
    await userEvent.click(await screen.findByRole('button', { name: /commencer la montée/i }));
    expect(await screen.findByText('En quelle année ?')).toBeInTheDocument();

    let resolveAnswer!: (value: unknown) => void;
    const pending = new Promise((resolve) => {
      resolveAnswer = resolve;
    });
    mockedApi.mockImplementation((url: string) =>
      url.includes('/answer/') ? pending : route(url),
    );

    await userEvent.click(screen.getByRole('button', { name: '1998' }));

    // The server round trip has not resolved yet — every option, including
    // the one just clicked, must refuse further clicks until it does.
    expect(screen.getByRole('button', { name: '1996' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '1998' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '2001' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '2004' })).toBeDisabled();

    resolveAnswer({
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
    expect(await screen.findByText(/\+1 dégâts/i)).toBeInTheDocument();
  });

  it('lets the timer expire again after a colliding cover question repeats (critical questionId regression)', async () => {
    // `cover` (and `most_popular`) reuse the exact same prompt for every
    // subject, so two consecutive tier-1 draws of the same archetype are
    // genuinely different questions that share tier, band, archetype AND
    // prompt — the only thing that differs is the options. If `questionId`
    // is built from anything but the options, the ring never resets: it
    // stays frozen wherever it was and `onExpire` never fires again.
    const COVER_PROMPT = 'Quelle œuvre cette jaquette annonce-t-elle ?';
    const COVER_Q1 = {
      tier: 1,
      band: 'A',
      timer: 1,
      damage: 1,
      limiter_break: false,
      streak: 0,
      run_damage: 0,
      best_tier: 0,
      archetype: 'cover',
      prompt: COVER_PROMPT,
      options: ['Solo Leveling', 'Frieren', 'Jujutsu Kaisen', 'Chainsaw Man'],
      image: 'cover-a.png',
    };
    const COVER_Q2 = {
      ...COVER_Q1,
      options: ['Vinland Saga', 'Spy x Family', 'Blue Lock', 'Oshi no Ko'],
      image: 'cover-b.png',
    };
    const WRONG_VERDICT = {
      correct: false,
      late: true,
      damage_dealt: 0,
      correct_index: 1,
      correct_label: 'Frieren',
      subject: 'Frieren',
      tier: 1,
      run_damage: 0,
      best_tier: 0,
      limiter_break: false,
      streak: 0,
      boss: { current_hp: 74000, total_hp: 100000, current_phase: 2, is_active: true },
    };

    let questionCalls = 0;
    mockedApi.mockImplementation((url: string) => {
      if (url.includes('/active/')) return Promise.resolve(BOSS);
      if (url.includes('/leaderboard/')) return Promise.resolve({ leaderboard: [] });
      if (url.includes('/question/')) {
        questionCalls += 1;
        return Promise.resolve(questionCalls === 1 ? COVER_Q1 : COVER_Q2);
      }
      if (url.includes('/answer/')) return Promise.resolve(WRONG_VERDICT);
      return Promise.resolve({});
    });

    renderPage();
    await userEvent.click(await screen.findByRole('button', { name: /commencer la montée/i }));
    expect(await screen.findByText(COVER_PROMPT)).toBeInTheDocument();

    // First question's timer runs out untouched — onExpire -> answer(-1).
    expect(
      await screen.findByRole('button', { name: /question suivante/i }, { timeout: 3000 }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /question suivante/i }));

    // Same prompt, tier, band and archetype as before — but a genuinely
    // different question (different options).
    expect(await screen.findByText(COVER_PROMPT)).toBeInTheDocument();

    // The ring must have reset and be able to expire a second time.
    expect(
      await screen.findByRole('button', { name: /question suivante/i }, { timeout: 3000 }),
    ).toBeInTheDocument();
  }, 10000);
});

describe('buildQuestionId', () => {
  const base = {
    tier: 1,
    band: 'A' as const,
    timer: 20,
    damage: 1,
    limiter_break: false,
    streak: 0,
    run_damage: 0,
    best_tier: 0,
    archetype: 'cover',
    prompt: 'Quelle œuvre cette jaquette annonce-t-elle ?',
    options: ['Solo Leveling', 'Frieren', 'Jujutsu Kaisen', 'Chainsaw Man'],
    image: null,
  };

  it('produces different ids for two different questions that share tier, band, archetype and prompt', () => {
    const other = {
      ...base,
      options: ['Vinland Saga', 'Spy x Family', 'Blue Lock', 'Oshi no Ko'],
    };
    expect(buildQuestionId(base)).not.toBe(buildQuestionId(other));
  });

  it('produces the same id when the backend re-issues the identical pending question verbatim', () => {
    const reissued = { ...base, options: [...base.options] };
    expect(buildQuestionId(base)).toBe(buildQuestionId(reissued));
  });

  it('returns an empty string when there is no question', () => {
    expect(buildQuestionId(null)).toBe('');
  });
});
