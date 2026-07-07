import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUndercoverRoom } from '../useUndercoverRoom';
import useSocket from '../useSocket';

vi.mock('../useSocket', () => ({
  default: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => ({ roomCode: 'ROOM123' }),
  useSearchParams: () => [new URLSearchParams()],
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: any) => typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));

const mockGameState = {
  players: [
    { id: '1', name: 'Alice', is_host: true, alive: true },
    { id: '2', name: 'Bob', alive: true },
  ],
  myId: '2',
  state: 'lobby',
  messages: [],
  categories: ['Anime'],
  difficulty: 'Normal',
  visibility: 'private',
  num_undercovers: 1,
  num_mrwhites: 0,
  round: 0,
};

describe('useUndercoverRoom hook', () => {
  const mockSendAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useSocket as any).mockReturnValue({
      gameState: mockGameState,
      connected: true,
      sendAction: mockSendAction,
    });
  });

  it('should initialize with values from useSocket', () => {
    const { result } = renderHook(() => useUndercoverRoom());

    expect(result.current.roomCode).toBe('ROOM123');
    expect(result.current.connected).toBe(true);
    expect(result.current.players).toHaveLength(2);
    expect(result.current.myId).toBe('2');
    expect(result.current.me?.name).toBe('Bob');
    expect(result.current.isHost).toBe(false);
  });

  it('should handle submitName correctly', () => {
    const { result } = renderHook(() => useUndercoverRoom());

    act(() => {
      result.current.setName('Charlie');
    });

    act(() => {
      result.current.submitName();
    });

    expect(mockSendAction).toHaveBeenCalledWith('set_name', { name: 'Charlie' });
  });

  it('should handle castVote correctly', () => {
    // Override myId to be '2' (alive)
    const { result } = renderHook(() => useUndercoverRoom());

    act(() => {
      result.current.castVote('1');
    });

    // Since state is 'lobby', it should not cast vote
    expect(mockSendAction).not.toHaveBeenCalled();
  });
});
