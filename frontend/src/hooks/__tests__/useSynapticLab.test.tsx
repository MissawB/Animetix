import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSynapticLab } from '../useSynapticLab';
import { apiClient } from '../../utils/apiClient';

vi.mock('../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const mockLabState = {
  status: 'active',
  weights: [
    [0.1, 0.2],
    [0.3, 0.4],
  ],
  concepts: ['ConceptA', 'ConceptB'],
  plasticity_config: { tau_plus: 20.0, tau_minus: 20.0, num_concepts: 2 },
  personalization_settings: {
    mode: 'auto',
    intensity_multiplier: 1.0,
    features: { aura: true, font: true, accent: true },
  },
  current_archetype: {
    id: 'shonen',
    accent: '#ff0000',
    aura_type: 'fire',
    intensity: 0.8,
    font_vibe: 'bold',
  },
};

describe('useSynapticLab hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should load unified state successfully', async () => {
    vi.mocked(apiClient).mockResolvedValue(mockLabState);

    const { result } = renderHook(() => useSynapticLab(), { wrapper: makeWrapper() });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.state).toEqual(mockLabState);
    expect(result.current.tauPlus).toBe(20.0);
    expect(result.current.tauMinus).toBe(20.0);
  });

  it('should handle local state updates', async () => {
    vi.mocked(apiClient).mockResolvedValue(mockLabState);

    const { result } = renderHook(() => useSynapticLab(), { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setTauPlus(30.0);
      result.current.setTauMinus(10.0);
      result.current.setMode('manual');
    });

    expect(result.current.tauPlus).toBe(30.0);
    expect(result.current.tauMinus).toBe(10.0);
    expect(result.current.mode).toBe('manual');
  });

  it('should mutate config when handleApplyConfig is called', async () => {
    vi.mocked(apiClient).mockResolvedValue(mockLabState);

    const { result } = renderHook(() => useSynapticLab(), { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleApplyConfig();
    });

    await waitFor(() => {
      expect(apiClient).toHaveBeenCalledWith(
        '/api/v1/singularity-lab/',
        expect.objectContaining({
          method: 'POST',
        }),
      );
    });
  });
});
