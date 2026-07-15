import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { socialService } from '../../services/socialService';
import { useLeaderboard } from '../useLeaderboard';
import { Profile } from '../../../../types';

vi.mock('../../services/socialService', () => ({
  socialService: {
    getLeaderboard: vi.fn(),
  },
}));
const mockedGetLeaderboard = vi.mocked(socialService.getLeaderboard);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useLeaderboard', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches the leaderboard', async () => {
    const board = [{ username: 'kira' }] as unknown as Profile[];
    mockedGetLeaderboard.mockResolvedValue(board);
    const { result } = renderHook(() => useLeaderboard(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedGetLeaderboard).toHaveBeenCalled();
    expect(result.current.data).toBe(board);
  });
});
