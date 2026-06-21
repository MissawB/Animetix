import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { ParadoxState } from '../../../../types';
import { paradoxService } from '../../services/paradoxService';
import { apiClient } from '../../../../utils/apiClient';
import { useParadoxStore } from '../paradoxStore';

vi.mock('../../services/paradoxService', () => ({
  paradoxService: {
    getState: vi.fn(),
    submit: vi.fn(),
  },
}));

vi.mock('../../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const mockedService = vi.mocked(paradoxService);
const mockedApiClient = vi.mocked(apiClient);

const makeState = (overrides: Partial<ParadoxState> = {}): ParadoxState =>
  ({
    items: [
      { id: 1, title: 'A', image: 'a.jpg' },
      { id: 2, title: 'B', image: 'b.jpg' },
    ],
    ...overrides,
  } as ParadoxState);

describe('useParadoxStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParadoxStore.setState({ gameState: null, isLoading: true, error: null });
  });

  it('initializes with null state and loading true', () => {
    const state = useParadoxStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('loadGame populates gameState from getState', async () => {
    const game = makeState();
    mockedService.getState.mockResolvedValue(game);

    await useParadoxStore.getState().loadGame();

    const state = useParadoxStore.getState();
    expect(state.gameState).toEqual(game);
    expect(state.isLoading).toBe(false);
    expect(mockedApiClient).not.toHaveBeenCalled();
  });

  it('loadGame falls back to apiClient start when getState rejects', async () => {
    mockedService.getState.mockRejectedValue(new Error('no game'));
    const fresh = makeState({ items: [{ id: 9, title: 'Z', image: 'z.jpg' }] });
    mockedApiClient.mockResolvedValue(fresh);

    await useParadoxStore.getState().loadGame();

    expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/game/paradox/start/', { method: 'POST' });
    expect(useParadoxStore.getState().gameState).toEqual(fresh);
    expect(useParadoxStore.getState().error).toBeNull();
  });

  it('loadGame sets error when both getState and fallback reject', async () => {
    mockedService.getState.mockRejectedValue(new Error('a'));
    mockedApiClient.mockRejectedValue(new Error('start failed'));

    await useParadoxStore.getState().loadGame();

    const state = useParadoxStore.getState();
    expect(state.gameState).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('start failed');
  });

  it('submitGuess sends intruder_id and updates gameState', async () => {
    const next = makeState({ items: [{ id: 3, title: 'C', image: 'c.jpg' }] });
    mockedService.submit.mockResolvedValue(next);

    await useParadoxStore.getState().submitGuess(2);

    expect(mockedService.submit).toHaveBeenCalledWith({ intruder_id: 2 });
    expect(useParadoxStore.getState().gameState).toEqual(next);
    expect(useParadoxStore.getState().isLoading).toBe(false);
  });

  it('submitGuess sets error on failure', async () => {
    mockedService.submit.mockRejectedValue(new Error('guess boom'));

    await useParadoxStore.getState().submitGuess(1);

    expect(useParadoxStore.getState().error).toBe('guess boom');
    expect(useParadoxStore.getState().isLoading).toBe(false);
  });
});
