import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '../../../../utils/apiClient';
import { useAdminEval } from '../useAdminEval';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApiClient = vi.mocked(apiClient);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useAdminEval', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and returns admin eval data via apiClient', async () => {
    const payload = { evals: [{ id: 1, score: 0.9 }] };
    mockedApiClient.mockResolvedValue(payload);

    const { result } = renderHook(() => useAdminEval(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/admin/ai_eval/data/');
    expect(result.current.data).toEqual(payload);
  });

  it('starts in a loading state', () => {
    mockedApiClient.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useAdminEval(), { wrapper: makeWrapper() });

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });
});
