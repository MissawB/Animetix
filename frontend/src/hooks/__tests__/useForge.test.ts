import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useForge } from '../useForge';
import { useAuthStore } from '../../store/authStore';
import { startFusion, getFusionStatus } from '../../api';
import type { FusionResponse, FusionStatus } from '../../api';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));

vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('../../api', () => ({
  startFusion: vi.fn(),
  getFusionStatus: vi.fn(),
}));

// The selector param type of the (overloaded) zustand hook, extracted structurally
// so we don't need to export the store's internal state interface just for tests.
type AuthStoreSelector = Parameters<typeof useAuthStore>[0];
type AuthStoreState = AuthStoreSelector extends (state: infer S) => unknown ? S : never;

describe('useForge hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize with default states', () => {
    vi.mocked(useAuthStore).mockImplementation((selector: AuthStoreSelector) =>
      selector({ isAuthenticated: true, user: { wallet_balance: 150 } } as AuthStoreState),
    );

    const { result } = renderHook(() => useForge());

    expect(result.current.itemA).toBeNull();
    expect(result.current.itemB).toBeNull();
    expect(result.current.chaosLevel).toBe(50);
    expect(result.current.balance).toBe(50);
    expect(result.current.artStyle).toBe('Cyberpunk');
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.walletBalance).toBe(150);
  });

  it('should handle setting values', () => {
    vi.mocked(useAuthStore).mockImplementation((selector: AuthStoreSelector) =>
      selector({ isAuthenticated: true, user: { wallet_balance: 150 } } as AuthStoreState),
    );

    const { result } = renderHook(() => useForge());

    act(() => {
      result.current.setChaosLevel(80);
      result.current.setBalance(30);
      result.current.setArtStyle('Ukiyo-e');
    });

    expect(result.current.chaosLevel).toBe(80);
    expect(result.current.balance).toBe(30);
    expect(result.current.artStyle).toBe('Ukiyo-e');
  });

  it('should reject starting fusion if not authenticated', async () => {
    vi.mocked(useAuthStore).mockImplementation((selector: AuthStoreSelector) =>
      selector({ isAuthenticated: false, user: null } as AuthStoreState),
    );

    const { result } = renderHook(() => useForge());

    await act(async () => {
      await result.current.handleStartFusion();
    });

    expect(result.current.error).toContain('Connexion requise');
    expect(result.current.isGenerating).toBe(false);
  });

  it('should start fusion and poll status until complete', async () => {
    vi.mocked(useAuthStore).mockImplementation((selector: AuthStoreSelector) =>
      selector({ isAuthenticated: true, user: { wallet_balance: 150 } } as AuthStoreState),
    );

    const mockStartRes = { task_id: 'task-123', fusion_id: 99 };
    vi.mocked(startFusion).mockResolvedValue(mockStartRes as FusionResponse);

    const mockStatusPending = { completed: false, status: 'processing' };
    const mockStatusComplete = { completed: true, status: 'success', output: 'result_url' };
    vi.mocked(getFusionStatus)
      .mockResolvedValueOnce(mockStatusPending as FusionStatus)
      .mockResolvedValueOnce(mockStatusComplete as unknown as FusionStatus);

    const { result } = renderHook(() => useForge());

    await act(async () => {
      await result.current.handleStartFusion();
    });

    expect(startFusion).toHaveBeenCalled();
    expect(result.current.isGenerating).toBe(true);
    expect(result.current.fusionData).toEqual(mockStartRes);

    // First poll
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(getFusionStatus).toHaveBeenCalledWith('task-123', 99);
    expect(result.current.isGenerating).toBe(true);

    // Second poll (completes)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(result.current.isGenerating).toBe(false);
    expect(result.current.showConfetti).toBe(true);
    expect(result.current.status).toEqual(mockStatusComplete);
  });

  it('should reset all states on resetForge', () => {
    vi.mocked(useAuthStore).mockImplementation((selector: AuthStoreSelector) =>
      selector({ isAuthenticated: true, user: { wallet_balance: 150 } } as AuthStoreState),
    );

    const { result } = renderHook(() => useForge());

    act(() => {
      result.current.setItemA({ id: '1', title: 'Item A', name: 'Item A', type: 'anime' });
      result.current.resetForge();
    });

    expect(result.current.itemA).toBeNull();
    expect(result.current.isGenerating).toBe(false);
  });
});
