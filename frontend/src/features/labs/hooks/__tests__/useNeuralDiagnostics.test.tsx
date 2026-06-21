import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useNeuralDiagnostics } from '../useNeuralDiagnostics';
import { labService } from '../../services/labService';

vi.mock('../../services/labService');

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useNeuralDiagnostics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('runs diagnostics and exposes the result', async () => {
    const report = { score: 0.42, findings: ['ok'] };
    (labService.runDiagnostics as Mock).mockResolvedValue(report);

    const { result } = renderHook(() => useNeuralDiagnostics(), { wrapper: makeWrapper() });

    expect(result.current.loading).toBe(false);

    await act(async () => {
      await result.current.runDiagnostic('check the graph');
    });

    expect(labService.runDiagnostics).toHaveBeenCalledWith('check the graph');
    await waitFor(() => expect(result.current.data).toEqual(report));
  });

  it('surfaces errors from the service', async () => {
    const err = new Error('diagnostics failed');
    (labService.runDiagnostics as Mock).mockRejectedValue(err);

    const { result } = renderHook(() => useNeuralDiagnostics(), { wrapper: makeWrapper() });

    await act(async () => {
      await expect(result.current.runDiagnostic('boom')).rejects.toThrow('diagnostics failed');
    });

    await waitFor(() => expect(result.current.error).toEqual(err));
  });
});
