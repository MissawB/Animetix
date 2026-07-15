import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { blindtestService } from '../blindtestService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('blindtestService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState normalizes the state endpoint response', async () => {
    mocked.mockResolvedValue({
      game_over: true,
      is_daily: false,
      video_url: 'v',
      theme_type: 'OP',
      guesses: [{ title: 'x', is_correct: false }],
    });

    const result = await blindtestService.getState();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/state/', { skipToast: true });
    expect(result.gameOver).toBe(true);
    expect(result.video_url).toBe('v');
    expect(result.theme_type).toBe('OP');
    expect(result.guesses).toEqual([{ title: 'x', is_correct: false }]);
  });

  it('startGame posts the chosen format/difficulty and normalizes', async () => {
    mocked.mockResolvedValue({ theme_type: 'OP', game_over: false, max_attempts: 3 });

    const result = await blindtestService.startGame({ type: 'OP', difficulty: 'Hard' });

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/start/', {
      method: 'POST',
      body: JSON.stringify({ is_daily: false, type: 'OP', difficulty: 'Hard' }),
    });
    expect(result.theme_type).toBe('OP');
    expect(result.maxAttempts).toBe(3);
  });

  it('submitGuess posts the guess and returns the result', async () => {
    mocked.mockResolvedValue({
      game_over: true,
      won: true,
      guesses: [{ title: 'One Piece', is_correct: true }],
      secret_title: 'One Piece',
      attempts_left: 3,
    });

    const result = await blindtestService.submitGuess('One Piece');

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/guess/', {
      method: 'POST',
      body: JSON.stringify({ guess: 'One Piece' }),
    });
    expect(result).toEqual({
      gameOver: true,
      won: true,
      guesses: [{ title: 'One Piece', is_correct: true }],
      secret_title: 'One Piece',
      attemptsLeft: 3,
    });
  });

  it('getTitles returns the title list', async () => {
    mocked.mockResolvedValue({ titles: ['Naruto', 'Bleach'] });

    const result = await blindtestService.getTitles();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/titles/', { skipToast: true });
    expect(result).toEqual(['Naruto', 'Bleach']);
  });

  it('getState rejects on invalid validation schemas', async () => {
    mocked.mockResolvedValue({
      game_over: 'not-a-boolean-invalid-data',
    });

    await expect(blindtestService.getState()).rejects.toThrow();
  });
});
