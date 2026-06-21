import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAdminEval } from '../useAdminEval';

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

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetches and returns admin eval data', async () => {
    const payload = { evals: [{ id: 1, score: 0.9 }] };
    const json = vi.fn().mockResolvedValue(payload);
    const fetchMock = vi.fn().mockResolvedValue({ json } as unknown as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useAdminEval(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/admin/ai_eval/data/');
    expect(result.current.data).toEqual(payload);
  });

  it('starts in a loading state', () => {
    const fetchMock = vi.fn().mockReturnValue(new Promise(() => {}));
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useAdminEval(), { wrapper: makeWrapper() });

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });
});
