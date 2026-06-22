import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '../../../../utils/apiClient';
import { useDPO } from '../useDPO';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useDPO', () => {
  beforeEach(() => vi.clearAllMocks());

  it('exposes feedbacks from the curation endpoint', async () => {
    mocked.mockResolvedValue([{ feedback_id: 1 }]);
    const { result } = renderHook(() => useDPO(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mocked).toHaveBeenCalledWith('/api/v1/mlops/dpo/curation/');
    expect(result.current.feedbacks).toEqual([{ feedback_id: 1 }]);
  });

  it('curate POSTs the chosen text', async () => {
    mocked.mockResolvedValue([]);
    const { result } = renderHook(() => useDPO(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.curate({ feedback_id: 5, chosen_text: 'better' });
    });

    await waitFor(() =>
      expect(mocked).toHaveBeenCalledWith('/api/v1/mlops/dpo/curation/', {
        method: 'POST',
        body: JSON.stringify({ feedback_id: 5, chosen_text: 'better' }),
      }),
    );
  });
});
