import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { socialService } from '../../services/socialService';
import { useSocialDashboard } from '../useSocialDashboard';

vi.mock('../../services/socialService', () => ({
  socialService: { getDashboard: vi.fn(), toggleFollow: vi.fn() },
}));
const getDashboard = vi.mocked(socialService.getDashboard);
const toggleFollow = vi.mocked(socialService.toggleFollow);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useSocialDashboard', () => {
  beforeEach(() => vi.clearAllMocks());

  it('loads the dashboard', async () => {
    const dash = { feed: [] } as unknown as Awaited<ReturnType<typeof socialService.getDashboard>>;
    getDashboard.mockResolvedValue(dash);
    const { result } = renderHook(() => useSocialDashboard(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toBe(dash);
  });

  it('toggleFollow calls the service', async () => {
    getDashboard.mockResolvedValue({} as unknown as Awaited<ReturnType<typeof socialService.getDashboard>>);
    toggleFollow.mockResolvedValue(undefined as unknown as Awaited<ReturnType<typeof socialService.toggleFollow>>);
    const { result } = renderHook(() => useSocialDashboard(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.toggleFollow(42);
    });

    await waitFor(() => expect(toggleFollow.mock.calls[0]?.[0]).toBe(42));
  });
});
