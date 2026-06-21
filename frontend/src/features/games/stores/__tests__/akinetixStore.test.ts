import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AkinetixState } from '../../../../types';
import { akinetixService } from '../../services/akinetixService';
import { useAkinetixStore } from '../akinetixStore';

vi.mock('../../services/akinetixService', () => ({
  akinetixService: {
    getState: vi.fn(),
    startGame: vi.fn(),
    submitAnswer: vi.fn(),
    submitConfirmation: vi.fn(),
  },
}));

const mockedService = vi.mocked(akinetixService);

const makeState = (overrides: Partial<AkinetixState> = {}): AkinetixState =>
  ({
    currentQuestion: 'Is your character a male?',
    history: [],
    aiGuess: null,
    ...overrides,
  } as AkinetixState);

describe('useAkinetixStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAkinetixStore.setState({ gameState: null, isLoading: true, error: null });
  });

  it('initializes with null game state, loading true, no error', () => {
    const state = useAkinetixStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('loadGame populates gameState from getState and clears loading', async () => {
    const game = makeState({ currentQuestion: 'Loaded?' });
    mockedService.getState.mockResolvedValue(game);

    await useAkinetixStore.getState().loadGame();

    const state = useAkinetixStore.getState();
    expect(state.gameState).toEqual(game);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
    expect(mockedService.startGame).not.toHaveBeenCalled();
  });

  it('loadGame falls back to startGame when getState rejects', async () => {
    mockedService.getState.mockRejectedValue(new Error('no active game'));
    const fresh = makeState({ currentQuestion: 'Started?' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useAkinetixStore.getState().loadGame();

    const state = useAkinetixStore.getState();
    expect(state.gameState).toEqual(fresh);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('loadGame sets error when both getState and startGame reject', async () => {
    mockedService.getState.mockRejectedValue(new Error('boom'));
    mockedService.startGame.mockRejectedValue(new Error('start failed'));

    await useAkinetixStore.getState().loadGame();

    const state = useAkinetixStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('start failed');
  });

  it('restartGame replaces gameState with a fresh game', async () => {
    useAkinetixStore.setState({ gameState: makeState({ currentQuestion: 'old' }) });
    const fresh = makeState({ currentQuestion: 'new' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useAkinetixStore.getState().restartGame();

    const state = useAkinetixStore.getState();
    expect(state.gameState).toEqual(fresh);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('restartGame sets error on failure', async () => {
    mockedService.startGame.mockRejectedValue(new Error('restart boom'));

    await useAkinetixStore.getState().restartGame();

    expect(useAkinetixStore.getState().error).toBe('restart boom');
    expect(useAkinetixStore.getState().isLoading).toBe(false);
  });

  it('submitAnswer updates gameState with the response', async () => {
    const next = makeState({ currentQuestion: 'next question', history: [{ q: 'q', a: 'yes' }] });
    mockedService.submitAnswer.mockResolvedValue(next);

    await useAkinetixStore.getState().submitAnswer('yes');

    expect(mockedService.submitAnswer).toHaveBeenCalledWith('yes');
    expect(useAkinetixStore.getState().gameState).toEqual(next);
    expect(useAkinetixStore.getState().isLoading).toBe(false);
  });

  it('submitAnswer sets error on failure', async () => {
    mockedService.submitAnswer.mockRejectedValue(new Error('answer boom'));

    await useAkinetixStore.getState().submitAnswer('no');

    expect(useAkinetixStore.getState().error).toBe('answer boom');
    expect(useAkinetixStore.getState().isLoading).toBe(false);
  });

  it('submitConfirmation restarts the game on success', async () => {
    mockedService.submitConfirmation.mockResolvedValue(undefined);
    const fresh = makeState({ currentQuestion: 'after confirm' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useAkinetixStore.getState().submitConfirmation(true, 'Naruto');

    expect(mockedService.submitConfirmation).toHaveBeenCalledWith(true, 'Naruto');
    expect(mockedService.startGame).toHaveBeenCalledTimes(1);
    expect(useAkinetixStore.getState().gameState).toEqual(fresh);
    expect(useAkinetixStore.getState().error).toBeNull();
  });

  it('submitConfirmation sets error and does not restart on failure', async () => {
    mockedService.submitConfirmation.mockRejectedValue(new Error('cheat detected'));

    await useAkinetixStore.getState().submitConfirmation(false);

    expect(mockedService.startGame).not.toHaveBeenCalled();
    expect(useAkinetixStore.getState().error).toBe('cheat detected');
    expect(useAkinetixStore.getState().isLoading).toBe(false);
  });
});
