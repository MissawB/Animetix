import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useToastStore } from '../toastStore';

describe('useToastStore', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useToastStore.setState({ toasts: [] });
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('starts with no toasts', () => {
    expect(useToastStore.getState().toasts).toEqual([]);
  });

  it('addToast appends a toast with a generated id and default "info" type', () => {
    useToastStore.getState().addToast('Hello');
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].message).toBe('Hello');
    expect(toasts[0].type).toBe('info');
    expect(toasts[0].id).toBeTruthy();
  });

  it('addToast respects an explicit type', () => {
    useToastStore.getState().addToast('Boom', 'error');
    expect(useToastStore.getState().toasts[0].type).toBe('error');
  });

  it('addToast assigns unique ids to multiple toasts', () => {
    useToastStore.getState().addToast('A', 'success');
    useToastStore.getState().addToast('B', 'info');
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(2);
    expect(toasts[0].id).not.toBe(toasts[1].id);
    expect(toasts.map((t) => t.message)).toEqual(['A', 'B']);
  });

  it('auto-removes a toast after 5 seconds', () => {
    useToastStore.getState().addToast('Temporary');
    expect(useToastStore.getState().toasts).toHaveLength(1);

    vi.advanceTimersByTime(4999);
    expect(useToastStore.getState().toasts).toHaveLength(1);

    vi.advanceTimersByTime(1);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('removeToast removes only the matching toast by id', () => {
    useToastStore.getState().addToast('Keep');
    useToastStore.getState().addToast('Drop');
    const [keep, drop] = useToastStore.getState().toasts;

    useToastStore.getState().removeToast(drop.id);
    const remaining = useToastStore.getState().toasts;
    expect(remaining).toHaveLength(1);
    expect(remaining[0].id).toBe(keep.id);
    expect(remaining[0].message).toBe('Keep');
  });

  it('removeToast is a no-op for an unknown id', () => {
    useToastStore.getState().addToast('Stay');
    useToastStore.getState().removeToast('does-not-exist');
    expect(useToastStore.getState().toasts).toHaveLength(1);
  });
});
