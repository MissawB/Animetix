import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { getProfile } from '../../../../api';
import { useProfile } from '../useProfile';

vi.mock('../../../../api', () => ({ getProfile: vi.fn() }));
const mockedGetProfile = vi.mocked(getProfile);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useProfile', () => {
  beforeEach(() => vi.clearAllMocks());

  it('is disabled when username is undefined', () => {
    const { result } = renderHook(() => useProfile(undefined), { wrapper: makeWrapper() });
    expect(mockedGetProfile).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('fetches the profile for a username', async () => {
    const profile = { username: 'kira' } as unknown as Awaited<ReturnType<typeof getProfile>>;
    mockedGetProfile.mockResolvedValue(profile);
    const { result } = renderHook(() => useProfile('kira'), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedGetProfile).toHaveBeenCalledWith('kira');
    expect(result.current.data).toBe(profile);
  });
});
