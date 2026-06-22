import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { adminService } from '../../services/adminService';
import { useHealth } from '../useHealth';

vi.mock('../../services/adminService', () => ({
  adminService: { getHealth: vi.fn() },
}));
const getHealth = vi.mocked(adminService.getHealth);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useHealth', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches the health status', async () => {
    const status = { status: 'ok' } as unknown as Awaited<ReturnType<typeof adminService.getHealth>>;
    getHealth.mockResolvedValue(status);
    const { result } = renderHook(() => useHealth(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getHealth).toHaveBeenCalled();
    expect(result.current.data).toBe(status);
  });
});
