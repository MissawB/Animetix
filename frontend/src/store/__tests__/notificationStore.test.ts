import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNotificationStore } from '../notificationStore';
import { useToastStore } from '../toastStore';

// A controllable fake WebSocket. The store assigns onopen/onmessage/onclose/
// onerror handlers after construction; tests fire those handlers manually to
// drive real state transitions in the store.
class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((e: unknown) => void) | null = null;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }
}

describe('useNotificationStore', () => {
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    FakeWebSocket.instances = [];
    originalWebSocket = global.WebSocket;
    // @ts-expect-error - assigning a controllable fake for the WebSocket global
    global.WebSocket = FakeWebSocket;

    // Deterministic ws URL.
    Object.defineProperty(window, 'location', {
      value: { protocol: 'http:', host: 'localhost:5173' },
      writable: true,
      configurable: true,
    });

    vi.useFakeTimers();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});

    useNotificationStore.setState({ unreadCount: 0, socket: null, isConnected: false });
    useToastStore.setState({ toasts: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    global.WebSocket = originalWebSocket;
  });

  it('connect: constructs a WebSocket with the derived ws URL', () => {
    useNotificationStore.getState().connect();

    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(FakeWebSocket.instances[0].url).toBe('ws://localhost:5173/ws/notifications/');
  });

  it('connect: uses wss:// when the page is served over https', () => {
    Object.defineProperty(window, 'location', {
      value: { protocol: 'https:', host: 'animetix.app' },
      writable: true,
      configurable: true,
    });

    useNotificationStore.getState().connect();
    expect(FakeWebSocket.instances[0].url).toBe('wss://animetix.app/ws/notifications/');
  });

  it('onopen: marks store connected and stores the socket', () => {
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];

    expect(useNotificationStore.getState().isConnected).toBe(false);
    ws.onopen?.();

    const state = useNotificationStore.getState();
    expect(state.isConnected).toBe(true);
    expect(state.socket).toBe(ws);
  });

  it('connect: is idempotent when a socket already exists', () => {
    useNotificationStore.getState().connect();
    FakeWebSocket.instances[0].onopen?.();

    // Second call should early-return (socket already set).
    useNotificationStore.getState().connect();
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it('onmessage: increments unread, dispatches a toast and a window event', () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    ws.onmessage?.({ data: JSON.stringify({ title: 'You were challenged' }) });
    ws.onmessage?.({ data: JSON.stringify({ title: 'New follower' }) });

    expect(useNotificationStore.getState().unreadCount).toBe(2);

    // Toast added with the message title.
    const toasts = useToastStore.getState().toasts;
    expect(toasts.map((t) => t.message)).toEqual(['You were challenged', 'New follower']);

    // Custom event dispatched for react-query invalidation.
    const events = dispatchSpy.mock.calls
      .map((c) => c[0])
      .filter((e): e is CustomEvent => e instanceof CustomEvent && e.type === 'animetix:new_notification');
    expect(events).toHaveLength(2);
    expect(events[0].detail).toEqual({ title: 'You were challenged' });
  });

  it('onmessage: malformed JSON does not throw and leaves unread untouched', () => {
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    expect(() => ws.onmessage?.({ data: 'not-json{' })).not.toThrow();
    expect(useNotificationStore.getState().unreadCount).toBe(0);
  });

  it('clearUnread: zeroes the count; incrementUnread/setUnreadCount adjust it', () => {
    const store = useNotificationStore.getState();
    store.setUnreadCount(5);
    expect(useNotificationStore.getState().unreadCount).toBe(5);

    store.incrementUnread();
    expect(useNotificationStore.getState().unreadCount).toBe(6);

    store.clearUnread();
    expect(useNotificationStore.getState().unreadCount).toBe(0);
  });

  it('disconnect: closes the socket and resets connection state', () => {
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    expect(useNotificationStore.getState().isConnected).toBe(true);

    useNotificationStore.getState().disconnect();

    expect(ws.close).toHaveBeenCalledWith(1000, 'User logged out');
    const state = useNotificationStore.getState();
    expect(state.socket).toBeNull();
    expect(state.isConnected).toBe(false);
  });

  it('disconnect: is a no-op when there is no socket', () => {
    expect(() => useNotificationStore.getState().disconnect()).not.toThrow();
    expect(useNotificationStore.getState().socket).toBeNull();
  });

  it('onclose: resets state then schedules a reconnect after 5s', () => {
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    ws.onclose?.();

    // Immediately after close: state reset, no new socket yet.
    expect(useNotificationStore.getState().isConnected).toBe(false);
    expect(useNotificationStore.getState().socket).toBeNull();
    expect(FakeWebSocket.instances).toHaveLength(1);

    // After the 5s retry timer a fresh socket is created.
    vi.advanceTimersByTime(5000);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });
});
