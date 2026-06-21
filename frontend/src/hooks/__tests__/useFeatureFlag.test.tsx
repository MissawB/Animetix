import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import posthog from 'posthog-js';
import { useFeatureFlag } from '../useFeatureFlag';

vi.mock('posthog-js', () => ({
  default: {
    isFeatureEnabled: vi.fn(),
    onFeatureFlags: vi.fn(),
  },
}));

const isFeatureEnabled = posthog.isFeatureEnabled as ReturnType<typeof vi.fn>;
const onFeatureFlags = posthog.onFeatureFlags as ReturnType<typeof vi.fn>;

describe('useFeatureFlag', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns the initial flag value from posthog.isFeatureEnabled', () => {
    isFeatureEnabled.mockReturnValue(true);
    const { result } = renderHook(() => useFeatureFlag('new-ui'));
    expect(result.current).toBe(true);
    expect(isFeatureEnabled).toHaveBeenCalledWith('new-ui');
  });

  it('returns false when the flag is disabled', () => {
    isFeatureEnabled.mockReturnValue(false);
    const { result } = renderHook(() => useFeatureFlag('new-ui'));
    expect(result.current).toBe(false);
  });

  it('returns undefined while flags are still loading', () => {
    isFeatureEnabled.mockReturnValue(undefined);
    const { result } = renderHook(() => useFeatureFlag('new-ui'));
    expect(result.current).toBeUndefined();
  });

  it('subscribes to flag updates and re-reads the value when they fire', () => {
    isFeatureEnabled.mockReturnValue(undefined);
    let registered: (() => void) | undefined;
    onFeatureFlags.mockImplementation((cb: () => void) => {
      registered = cb;
    });

    const { result } = renderHook(() => useFeatureFlag('new-ui'));
    expect(result.current).toBeUndefined();
    expect(onFeatureFlags).toHaveBeenCalledTimes(1);

    // Flags load -> the flag becomes enabled.
    isFeatureEnabled.mockReturnValue(true);
    act(() => {
      registered?.();
    });

    expect(result.current).toBe(true);
  });

  it('re-subscribes when the flag name changes', () => {
    isFeatureEnabled.mockReturnValue(false);
    const { rerender } = renderHook(({ flag }) => useFeatureFlag(flag), {
      initialProps: { flag: 'flag-a' },
    });
    expect(onFeatureFlags).toHaveBeenCalledTimes(1);

    rerender({ flag: 'flag-b' });
    expect(onFeatureFlags).toHaveBeenCalledTimes(2);
    expect(isFeatureEnabled).toHaveBeenCalledWith('flag-b');
  });
});
