import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { useWorldBossRun } from '../useWorldBossRun';
import { apiClient } from '../../../../utils/apiClient';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApi = vi.mocked(apiClient);

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

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
);

describe('useWorldBossRun', () => {
  beforeEach(() => vi.clearAllMocks());

  it('asks for a question and holds it', async () => {
    mockedApi.mockResolvedValue(QUESTION);
    const { result } = renderHook(() => useWorldBossRun(), { wrapper });

    act(() => result.current.start());

    await waitFor(() => expect(result.current.question?.prompt).toBe('En quelle année ?'));
    expect(result.current.phase).toBe('asking');
    expect(mockedApi).toHaveBeenCalledWith(
      '/api/v1/game/world-boss/question/',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('sends only the index it picked — never the answer', async () => {
    mockedApi.mockResolvedValueOnce(QUESTION);
    const { result } = renderHook(() => useWorldBossRun(), { wrapper });
    act(() => result.current.start());
    await waitFor(() => expect(result.current.question).not.toBeNull());

    mockedApi.mockResolvedValueOnce({ ...VERDICT, correct: true });
    act(() => result.current.answer(1));

    await waitFor(() => expect(result.current.phase).toBe('revealed'));
    const [, options] = mockedApi.mock.calls[1];
    expect(JSON.parse(options!.body as string)).toEqual({ index: 1 });
  });

  it('reveals the verdict, then clears it on the next question', async () => {
    mockedApi.mockResolvedValueOnce(QUESTION).mockResolvedValueOnce(VERDICT);
    const { result } = renderHook(() => useWorldBossRun(), { wrapper });
    act(() => result.current.start());
    await waitFor(() => expect(result.current.question).not.toBeNull());
    act(() => result.current.answer(0));
    await waitFor(() => expect(result.current.verdict?.correct).toBe(false));

    mockedApi.mockResolvedValueOnce({ ...QUESTION, tier: 1 });
    act(() => result.current.next());

    await waitFor(() => expect(result.current.verdict).toBeNull());
  });

  it('answering twice does not fire two requests', async () => {
    mockedApi.mockResolvedValueOnce(QUESTION);
    const { result } = renderHook(() => useWorldBossRun(), { wrapper });
    act(() => result.current.start());
    await waitFor(() => expect(result.current.question).not.toBeNull());

    mockedApi.mockResolvedValue(VERDICT);
    act(() => {
      result.current.answer(0);
      result.current.answer(2);
    });

    await waitFor(() => expect(result.current.phase).toBe('revealed'));
    expect(mockedApi.mock.calls.filter(([url]) => url.endsWith('/answer/'))).toHaveLength(1);
  });
});

const VERDICT = {
  correct: false,
  late: false,
  damage_dealt: 0,
  correct_index: 1,
  correct_label: '1998',
  subject: 'Cowboy Bebop',
  tier: 1,
  run_damage: 0,
  best_tier: 0,
  limiter_break: false,
  streak: 0,
  boss: { current_hp: 99999, total_hp: 100000, current_phase: 1, is_active: true },
};
