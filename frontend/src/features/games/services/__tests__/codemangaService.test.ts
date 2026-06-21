import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { codemangaService, type CodeMangaState, type CodeMangaAction } from '../codemangaService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeState = (): CodeMangaState => ({
  room_code: 'ABC',
  players: [],
  is_game_over: false,
});

describe('codemangaService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState fetches the room by code', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await codemangaService.getState('ABC');

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/codemanga/room/ABC');
    expect(result).toBe(state);
  });

  it('submit posts the action', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);
    const action: CodeMangaAction = { type: 'play', card: 1 };

    const result = await codemangaService.submit(action);

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/codemanga/action/', {
      method: 'POST',
      body: JSON.stringify(action),
    });
    expect(result).toBe(state);
  });
});
