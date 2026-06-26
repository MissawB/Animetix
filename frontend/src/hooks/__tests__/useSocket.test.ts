import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest';
import useSocket from '../useSocket';
import { useToastStore } from '../../store/toastStore';

// Mock the toast store
vi.mock('../../store/toastStore');

const mockAddToast = vi.fn();

// Mock WebSocket class
class MockWebSocket {
  url: string;
  readyState: number = 0; // CONNECTING
  onopen: (() => void) | null = null;
  onclose: ((event: { code: number; reason: string }) => void) | null = null;
  onerror: ((err: Event) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  send = vi.fn();
  close = vi.fn();
  static instances: MockWebSocket[] = [];

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url: string) {
    this.url = url;
    this.readyState = 0;
    MockWebSocket.instances.push(this);
  }

  // Helper method to simulate opening
  triggerOpen() {
    this.readyState = 1; // OPEN
    if (this.onopen) this.onopen();
  }

  // Helper method to simulate closing
  triggerClose(code: number) {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose({ code, reason: 'Mock closed' });
  }

  // Helper method to simulate message
  triggerMessage(data: unknown) {
    if (this.onmessage) this.onmessage({ data: JSON.stringify(data) });
  }
}

describe('useSocket', () => {
  let originalWebSocket: typeof global.WebSocket;

  beforeEach(() => {
    originalWebSocket = global.WebSocket;
    global.WebSocket = MockWebSocket as unknown as typeof global.WebSocket;
    MockWebSocket.instances = [];
    (useToastStore as unknown as Mock).mockReturnValue({ addToast: mockAddToast });
    mockAddToast.mockClear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('does not connect if roomCode is not provided', () => {
    const { result } = renderHook(() => useSocket(undefined, 'undercover'));
    expect(result.current.connected).toBe(false);
    expect(MockWebSocket.instances.length).toBe(0);
  });

  it('connects to WebSocket and initializes successfully', async () => {
    const { result } = renderHook(() => useSocket('room-1', 'undercover'));

    expect(MockWebSocket.instances.length).toBe(1);
    const socket = MockWebSocket.instances[0];
    expect(socket.url).toBe('ws://localhost:3000/ws/undercover/room-1/');

    // Trigger open
    act(() => {
      socket.triggerOpen();
    });

    expect(result.current.connected).toBe(true);
    expect(result.current.reconnecting).toBe(false);
    expect(socket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'action', action: 'sync_state' })
    );
  });

  it('receives game state updates', async () => {
    const { result } = renderHook(() => useSocket('room-1', 'undercover'));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.triggerOpen();
    });

    const mockState = { players: [], phase: 'voting' };
    act(() => {
      socket.triggerMessage({ type: 'game_state_update', state: mockState });
    });

    expect(result.current.gameState).toEqual(mockState);
  });

  it('receives chat messages', async () => {
    const { result } = renderHook(() => useSocket('room-1', 'undercover'));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.triggerOpen();
    });

    const mockMessage = { sender: 'haruhi', text: 'hello!' };
    act(() => {
      socket.triggerMessage({ type: 'chat_message', message: mockMessage });
    });

    expect(result.current.messages).toEqual([mockMessage]);
  });

  it('sends action messages immediately when connected', async () => {
    const { result } = renderHook(() => useSocket('room-1', 'undercover'));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.triggerOpen();
    });

    act(() => {
      result.current.sendAction('submit_word', { word: 'apple' });
    });

    expect(socket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'action', action: 'submit_word', word: 'apple' })
    );
  });

  it('queues messages when not connected and flushes them on open', async () => {
    const { result } = renderHook(() => useSocket('room-1', 'undercover'));
    const socket = MockWebSocket.instances[0];

    act(() => {
      result.current.sendAction('submit_word', { word: 'banana' });
    });

    expect(socket.send).not.toHaveBeenCalledWith(
      JSON.stringify({ type: 'action', action: 'submit_word', word: 'banana' })
    );

    act(() => {
      socket.triggerOpen();
    });

    expect(socket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'action', action: 'submit_word', word: 'banana' })
    );
  });

  it('handles clean up and closes the connection on unmount', () => {
    const { unmount } = renderHook(() => useSocket('room-1', 'undercover'));
    const socket = MockWebSocket.instances[0];

    unmount();

    expect(socket.close).toHaveBeenCalledWith(1000, 'Component unmounted');
  });

  it('reconnects when connection is lost', async () => {
    const { result } = renderHook(() => useSocket('room-1', 'undercover'));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.triggerOpen();
    });

    // Close unexpectedly
    act(() => {
      socket.triggerClose(1006);
    });

    expect(result.current.connected).toBe(false);
    expect(result.current.reconnecting).toBe(true);
    expect(mockAddToast).toHaveBeenCalledWith(
      'Connexion perdue. Tentative de reconnexion...',
      'info'
    );

    // Reconnection is scheduled (exponential delay: 1000 * 2^0 = 1000ms)
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // A new WebSocket instance should be created for reconnection
    expect(MockWebSocket.instances.length).toBe(2);
    const newSocket = MockWebSocket.instances[1];

    act(() => {
      newSocket.triggerOpen();
    });

    expect(result.current.connected).toBe(true);
    expect(result.current.reconnecting).toBe(false);
  });
});
