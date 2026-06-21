import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { BlindtestState } from '../../../../types';
import { blindtestService } from '../../services/blindtestService';
import { useBlindtestStore } from '../blindtestStore';

vi.mock('../../services/blindtestService', () => ({
  blindtestService: {
    getState: vi.fn(),
    startGame: vi.fn(),
    submitGuess: vi.fn(),
  },
}));

const mockedService = vi.mocked(blindtestService);

const makeState = (overrides: Partial<BlindtestState> = {}): BlindtestState =>
  ({
    guesses: [],
    ...overrides,
  } as BlindtestState);

describe('useBlindtestStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBlindtestStore.setState({ gameState: null, isLoading: true, error: null });
  });

  it('initializes with null state and loading true', () => {
    const state = useBlindtestStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('loadGame populates gameState from getState', async () => {
    const game = makeState({ video_url: 'http://v/1' });
    mockedService.getState.mockResolvedValue(game);

    await useBlindtestStore.getState().loadGame();

    const state = useBlindtestStore.getState();
    expect(state.gameState).toEqual(game);
    expect(state.isLoading).toBe(false);
    expect(mockedService.startGame).not.toHaveBeenCalled();
  });

  it('loadGame falls back to startGame when getState rejects', async () => {
    mockedService.getState.mockRejectedValue(new Error('no game'));
    const fresh = makeState({ video_url: 'http://v/2' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useBlindtestStore.getState().loadGame();

    expect(useBlindtestStore.getState().gameState).toEqual(fresh);
    expect(useBlindtestStore.getState().error).toBeNull();
  });

  it('loadGame sets error when both calls reject', async () => {
    mockedService.getState.mockRejectedValue(new Error('a'));
    mockedService.startGame.mockRejectedValue(new Error('start failed'));

    await useBlindtestStore.getState().loadGame();

    const state = useBlindtestStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('start failed');
  });

  it('restartGame replaces gameState with fresh game', async () => {
    useBlindtestStore.setState({ gameState: makeState({ video_url: 'old' }) });
    const fresh = makeState({ video_url: 'new' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useBlindtestStore.getState().restartGame();

    expect(useBlindtestStore.getState().gameState).toEqual(fresh);
    expect(useBlindtestStore.getState().isLoading).toBe(false);
  });

  it('restartGame sets error on failure', async () => {
    mockedService.startGame.mockRejectedValue(new Error('restart boom'));

    await useBlindtestStore.getState().restartGame();

    expect(useBlindtestStore.getState().error).toBe('restart boom');
    expect(useBlindtestStore.getState().isLoading).toBe(false);
  });

  it('submitGuess updates gameState with response', async () => {
    const next = makeState({ guesses: [{ title: 'Bleach', is_correct: false }] });
    mockedService.submitGuess.mockResolvedValue(next);

    await useBlindtestStore.getState().submitGuess('Bleach');

    expect(mockedService.submitGuess).toHaveBeenCalledWith('Bleach');
    expect(useBlindtestStore.getState().gameState).toEqual(next);
    expect(useBlindtestStore.getState().isLoading).toBe(false);
  });

  it('submitGuess sets error on failure', async () => {
    mockedService.submitGuess.mockRejectedValue(new Error('guess boom'));

    await useBlindtestStore.getState().submitGuess('x');

    expect(useBlindtestStore.getState().error).toBe('guess boom');
    expect(useBlindtestStore.getState().isLoading).toBe(false);
  });
});
