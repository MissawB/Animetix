import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import ClubChat from '../ClubChat';
import { useAuthStore } from '../../../../store/authStore';

// Mock the global WebSocket object
class MockWebSocket {
  url: string;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((err: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  send = vi.fn();
  close = vi.fn();
  static instances: MockWebSocket[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // Auto-open connection in microtask
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }
}

describe('ClubChat Component', () => {
  let originalWebSocket: typeof global.WebSocket;

  beforeEach(() => {
    originalWebSocket = global.WebSocket;
    global.WebSocket = MockWebSocket as unknown as typeof global.WebSocket;
    MockWebSocket.instances = [];

    // Set authenticated user in authStore
    useAuthStore.setState({
      user: {
        id: 1,
        username: 'testuser',
        email: 'testuser@animetix.com',
        is_authenticated: true,
      },
      isAuthenticated: true,
      isLoading: false,
    });
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    vi.restoreAllMocks();
  });

  it('renders the chat header and welcome message', async () => {
    render(<ClubChat clubId="1" clubName="Anime Explorers" />);

    // Check header
    expect(screen.getByText('Anime Explorers Chat')).toBeInTheDocument();

    // Check system welcome message
    expect(screen.getByText('Welcome to the Anime Explorers chat!')).toBeInTheDocument();
  });

  it('connects to the WebSocket and displays connected status', async () => {
    render(<ClubChat clubId="123" clubName="Otaku Lounge" />);

    // Wait for the websocket mock connection to establish
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    expect(MockWebSocket.instances.length).toBe(1);
    expect(MockWebSocket.instances[0].url).toContain('/ws/club/123/');
  });

  it('receives message from WebSocket and displays it', async () => {
    render(<ClubChat clubId="1" clubName="Test Club" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    const socketInstance = MockWebSocket.instances[0];

    // Simulate receiving a message from another user
    const otherUserMsg = {
      type: 'chat',
      username: 'haruhi',
      text: 'Welcome to the SOS Brigade!',
      club_id: '1',
    };

    fireEvent(
      window,
      new MessageEvent('message', {
        data: JSON.stringify(otherUserMsg),
      })
    );

    // Call onmessage directly on the mock instance since MessageEvent on window might not trigger it
    if (socketInstance.onmessage) {
      act(() => {
        socketInstance.onmessage!({ data: JSON.stringify(otherUserMsg) } as MessageEvent);
      });
    }

    await waitFor(() => {
      expect(screen.getByText('Welcome to the SOS Brigade!')).toBeInTheDocument();
      expect(screen.getByText('haruhi')).toBeInTheDocument();
    });
  });

  it('sends message via WebSocket and clears input on submit', async () => {
    render(<ClubChat clubId="1" clubName="Test Club" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    const socketInstance = MockWebSocket.instances[0];
    const input = screen.getByPlaceholderText('Type a message...');
    const form = input.closest('form');

    fireEvent.change(input, { target: { value: 'Hello WebSockets!' } });
    expect(input).toHaveValue('Hello WebSockets!');

    if (form) {
      fireEvent.submit(form);
    }

    expect(socketInstance.send).toHaveBeenCalledWith(
      JSON.stringify({ message: 'Hello WebSockets!' })
    );
    expect(input).toHaveValue('');
  });
});
