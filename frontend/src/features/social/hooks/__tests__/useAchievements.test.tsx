import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { socialService } from '../../services/socialService';
import { useAchievements } from '../useAchievements';

vi.mock('../../services/socialService', () => ({
  socialService: {
    getAchievements: vi.fn(),
  },
}));
const mocked = vi.mocked(socialService.getAchievements);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useAchievements', () => {
  beforeEach(() => vi.clearAllMocks());

  it('unwraps a paginated { results } payload', async () => {
    mocked.mockResolvedValue({ results: [{ id: 1 }] });
    const { result } = renderHook(() => useAchievements(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mocked).toHaveBeenCalled();
    expect(result.current.data).toEqual([{ id: 1 }]);
  });

  it('returns a bare array payload as-is', async () => {
    mocked.mockResolvedValue([{ id: 2 }]);
    const { result } = renderHook(() => useAchievements(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: 2 }]);
  });
});
