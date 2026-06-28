import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { akinetixService } from '../akinetixService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);

describe('akinetixService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState reads the state endpoint and normalizes the response', async () => {
    mocked.mockResolvedValue({
      current_question: 'Est-ce une Romance ?',
      game_over: false,
      ai_guess: null,
      history: [{ q: 'x', a: 'OUI' }],
    });
    const result = await akinetixService.getState();
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/state/');
    expect(result.currentQuestion).toBe('Est-ce une Romance ?');
    expect(result.gameOver).toBe(false);
    expect(result.history).toEqual([{ q: 'x', a: 'OUI' }]);
  });

  it('startGame POSTs to start', async () => {
    mocked.mockResolvedValue({});
    await akinetixService.startGame();
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/start/', { method: 'POST' });
  });

  it('submitAnswer POSTs the answer', async () => {
    mocked.mockResolvedValue({});
    await akinetixService.submitAnswer('Naruto');
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/answer/', {
      method: 'POST',
      body: JSON.stringify({ answer: 'Naruto' }),
    });
  });

  it('submitConfirmation POSTs correctness and target', async () => {
    mocked.mockResolvedValue(undefined);
    await akinetixService.submitConfirmation(true, 'Naruto');
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/confirm/', {
      method: 'POST',
      body: JSON.stringify({ correct: true, actual_target: 'Naruto' }),
    });
  });
});
