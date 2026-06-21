import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { vsBattleService } from '../vsBattleService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('vsBattleService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getArenaFeed fetches the arena endpoint', async () => {
    const feed = [{ id: 1 }];
    mocked.mockResolvedValue(feed);

    const result = await vsBattleService.getArenaFeed();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vs_battle/arena/');
    expect(result).toBe(feed);
  });

  it('runBattle posts both characters with optional franchises', async () => {
    const battle = { winner: 'A' };
    mocked.mockResolvedValue(battle);

    const result = await vsBattleService.runBattle('Goku', 'Saitama', 'DBZ', 'OPM');

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vs_battle/run/', {
      method: 'POST',
      body: JSON.stringify({
        char_a: 'Goku',
        char_b: 'Saitama',
        char_a_franchise: 'DBZ',
        char_b_franchise: 'OPM',
      }),
      headers: { 'Content-Type': 'application/json' },
    });
    expect(result).toBe(battle);
  });

  it('runBattle omits undefined franchises from the body', async () => {
    mocked.mockResolvedValue({});

    await vsBattleService.runBattle('Goku', 'Saitama');

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vs_battle/run/', {
      method: 'POST',
      body: JSON.stringify({
        char_a: 'Goku',
        char_b: 'Saitama',
        char_a_franchise: undefined,
        char_b_franchise: undefined,
      }),
      headers: { 'Content-Type': 'application/json' },
    });
  });

  it('likeBattle posts to the like endpoint for the id', async () => {
    const res = { status: 'ok' };
    mocked.mockResolvedValue(res);

    const result = await vsBattleService.likeBattle(42);

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vs_battle/42/like/', { method: 'POST' });
    expect(result).toBe(res);
  });
});
