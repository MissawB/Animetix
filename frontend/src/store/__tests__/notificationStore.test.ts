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
  onclose: ((e?: { code?: number }) => void) | null = null;
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
      .filter(
        (e): e is CustomEvent => e instanceof CustomEvent && e.type === 'animetix:new_notification',
      );
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

  it('onclose: schedules reconnect with exponential backoff and limits to 5 attempts', () => {
    useNotificationStore.getState().connect();
    const ws1 = FakeWebSocket.instances[0];
    ws1.onopen?.();

    // 1st close (unexpected, code 1006)
    ws1.onclose?.({ code: 1006 });
    expect(useNotificationStore.getState().isConnected).toBe(false);
    expect(useNotificationStore.getState().isReconnecting).toBe(true);

    // Delay should be 1000 * 2^0 = 1000ms
    vi.advanceTimersByTime(999);
    expect(FakeWebSocket.instances).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(FakeWebSocket.instances).toHaveLength(2);

    const ws2 = FakeWebSocket.instances[1];
    expect(useNotificationStore.getState().reconnectAttempts).toBe(1);

    // 2nd close
    ws2.onclose?.({ code: 1006 });
    // Delay should be 1000 * 2^1 = 2000ms
    vi.advanceTimersByTime(1999);
    expect(FakeWebSocket.instances).toHaveLength(2);
    vi.advanceTimersByTime(1);
    expect(FakeWebSocket.instances).toHaveLength(3);

    const ws3 = FakeWebSocket.instances[2];
    expect(useNotificationStore.getState().reconnectAttempts).toBe(2);

    // Reconnect success!
    ws3.onopen?.();
    expect(useNotificationStore.getState().isConnected).toBe(true);
    expect(useNotificationStore.getState().isReconnecting).toBe(false);
    expect(useNotificationStore.getState().reconnectAttempts).toBe(0);

    const toasts = useToastStore.getState().toasts;
    expect(toasts.some((t) => t.message.includes('rétablie'))).toBe(true);
  });

  it('onclose: does not reconnect on voluntary close (code 1000)', () => {
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    ws.onclose?.({ code: 1000 });
    expect(useNotificationStore.getState().isConnected).toBe(false);
    expect(useNotificationStore.getState().isReconnecting).toBe(false);

    vi.advanceTimersByTime(10000);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it('onclose: stops trying and shows error toast after 5 failed attempts', () => {
    useNotificationStore.getState().connect();

    // Simulate 5 failures (socket close without ever opening)
    for (let i = 0; i < 5; i++) {
      expect(FakeWebSocket.instances).toHaveLength(i + 1);
      const ws = FakeWebSocket.instances[i];
      ws.onclose?.({ code: 1006 });

      const delay = 1000 * Math.pow(2, i);
      vi.advanceTimersByTime(delay);
    }

    expect(FakeWebSocket.instances).toHaveLength(6);
    const lastWs = FakeWebSocket.instances[5];
    lastWs.onclose?.({ code: 1006 });

    // Now reconnectAttempts is 5, it should not schedule reconnect
    expect(useNotificationStore.getState().isReconnecting).toBe(false);
    const toasts = useToastStore.getState().toasts;
    expect(toasts.some((t) => t.message.includes('Impossible de se connecter'))).toBe(true);
  });

  it('disconnect: cancels pending reconnection timers', () => {
    useNotificationStore.getState().connect();
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    ws.onclose?.({ code: 1006 });

    expect(useNotificationStore.getState().isReconnecting).toBe(true);

    useNotificationStore.getState().disconnect();
    expect(useNotificationStore.getState().isReconnecting).toBe(false);

    vi.advanceTimersByTime(5000);
    // No new connection attempt
    expect(FakeWebSocket.instances).toHaveLength(1);
  });
});
