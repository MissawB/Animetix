import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '../../../../utils/apiClient';
import { useAchievements } from '../useAchievements';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);

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
    expect(mocked).toHaveBeenCalledWith('/api/v1/achievements/');
    expect(result.current.data).toEqual([{ id: 1 }]);
  });

  it('returns a bare array payload as-is', async () => {
    mocked.mockResolvedValue([{ id: 2 }]);
    const { result } = renderHook(() => useAchievements(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: 2 }]);
  });
});
