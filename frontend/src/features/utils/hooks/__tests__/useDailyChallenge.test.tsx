import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { utilsService } from '../../services/utilsService';
import { useDailyChallenge } from '../useDailyChallenge';

vi.mock('../../services/utilsService', () => ({
  utilsService: { getDaily: vi.fn() },
}));
const getDaily = vi.mocked(utilsService.getDaily);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useDailyChallenge', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches the daily challenge', async () => {
    const daily = { id: 1 };
    getDaily.mockResolvedValue(daily);
    const { result } = renderHook(() => useDailyChallenge(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getDaily).toHaveBeenCalled();
    expect(result.current.data).toBe(daily);
  });
});
