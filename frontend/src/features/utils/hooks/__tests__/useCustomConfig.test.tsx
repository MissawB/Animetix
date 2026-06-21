import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCustomConfig } from '../useCustomConfig';
import { utilsService } from '../../services/utilsService';
import { useToastStore } from '../../../../store/toastStore';
import { useAuthStore } from '../../../../store/authStore';
import { UserConfig } from '../../../../types';

vi.mock('../../services/utilsService');
vi.mock('../../../../store/toastStore');
vi.mock('../../../../store/authStore');

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const addToast = vi.fn();

const mockConfig = (): UserConfig => ({
  difficulty: 'Normal',
  theme: 'dark',
  notifications_enabled: true,
  ai_personality: 'friendly',
});

// useAuthStore is used as a selector: useAuthStore((s) => s.isAuthenticated)
const setAuthenticated = (value: boolean) => {
  (useAuthStore as unknown as Mock).mockImplementation(
    (selector: (state: { isAuthenticated: boolean }) => unknown) =>
      selector({ isAuthenticated: value })
  );
};

describe('useCustomConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useToastStore as unknown as Mock).mockReturnValue({ addToast });
    setAuthenticated(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches config when authenticated', async () => {
    const config = mockConfig();
    (utilsService.getConfig as Mock).mockResolvedValue(config);

    const { result } = renderHook(() => useCustomConfig(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.config).toEqual(config);
    expect(utilsService.getConfig).toHaveBeenCalled();
  });

  it('does not fetch config when not authenticated', async () => {
    setAuthenticated(false);
    (utilsService.getConfig as Mock).mockResolvedValue(mockConfig());

    renderHook(() => useCustomConfig(), { wrapper: makeWrapper() });

    // query disabled -> service never invoked
    await waitFor(() => expect(utilsService.getConfig).not.toHaveBeenCalled());
  });

  it('posts new config and shows a success toast on save', async () => {
    (utilsService.getConfig as Mock).mockResolvedValue(mockConfig());
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true } as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useCustomConfig(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.saveConfig({ theme: 'light' });
    });

    await waitFor(() => expect(addToast).toHaveBeenCalledWith('Paramètres enregistrés !', 'success'));
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/custom-config/',
      expect.objectContaining({ method: 'POST' })
    );

    vi.unstubAllGlobals();
  });
});
