import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { VisionState } from '../../../../types';
import { visionService } from '../../services/visionService';
import { useVisionStore } from '../visionStore';

vi.mock('../../services/visionService', () => ({
  visionService: {
    getState: vi.fn(),
    startGame: vi.fn(),
    submitGuess: vi.fn(),
  },
}));

const mockedService = vi.mocked(visionService);

const makeState = (overrides: Partial<VisionState> = {}): VisionState =>
  ({
    image_url: 'http://img/1',
    best_score: 0,
    guesses: [],
    ...overrides,
  } as VisionState);

describe('useVisionStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useVisionStore.setState({ gameState: null, isLoading: true, error: null });
  });

  it('initializes with null state and loading true', () => {
    const state = useVisionStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('loadGame populates gameState from getState', async () => {
    const game = makeState({ image_url: 'http://img/loaded' });
    mockedService.getState.mockResolvedValue(game);

    await useVisionStore.getState().loadGame();

    const state = useVisionStore.getState();
    expect(state.gameState).toEqual(game);
    expect(state.isLoading).toBe(false);
    expect(mockedService.startGame).not.toHaveBeenCalled();
  });

  it('loadGame falls back to startGame when getState rejects', async () => {
    mockedService.getState.mockRejectedValue(new Error('no game'));
    const fresh = makeState({ image_url: 'http://img/fresh' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useVisionStore.getState().loadGame();

    expect(useVisionStore.getState().gameState).toEqual(fresh);
    expect(useVisionStore.getState().error).toBeNull();
  });

  it('loadGame sets error when both calls reject', async () => {
    mockedService.getState.mockRejectedValue(new Error('a'));
    mockedService.startGame.mockRejectedValue(new Error('start failed'));

    await useVisionStore.getState().loadGame();

    const state = useVisionStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('start failed');
  });

  it('restartGame replaces gameState with fresh game', async () => {
    useVisionStore.setState({ gameState: makeState({ image_url: 'old' }) });
    const fresh = makeState({ image_url: 'new' });
    mockedService.startGame.mockResolvedValue(fresh);

    await useVisionStore.getState().restartGame();

    expect(useVisionStore.getState().gameState).toEqual(fresh);
    expect(useVisionStore.getState().isLoading).toBe(false);
  });

  it('restartGame sets error on failure', async () => {
    mockedService.startGame.mockRejectedValue(new Error('restart boom'));

    await useVisionStore.getState().restartGame();

    expect(useVisionStore.getState().error).toBe('restart boom');
    expect(useVisionStore.getState().isLoading).toBe(false);
  });

  it('submitGuess passes description and updates gameState', async () => {
    const next = makeState({ best_score: 80, guesses: [{ text: 'a battle scene', score: 80 }] });
    mockedService.submitGuess.mockResolvedValue(next);

    await useVisionStore.getState().submitGuess('a battle scene');

    expect(mockedService.submitGuess).toHaveBeenCalledWith('a battle scene');
    expect(useVisionStore.getState().gameState).toEqual(next);
    expect(useVisionStore.getState().isLoading).toBe(false);
  });

  it('submitGuess sets error on failure', async () => {
    mockedService.submitGuess.mockRejectedValue(new Error('guess boom'));

    await useVisionStore.getState().submitGuess('x');

    expect(useVisionStore.getState().error).toBe('guess boom');
    expect(useVisionStore.getState().isLoading).toBe(false);
  });
});
