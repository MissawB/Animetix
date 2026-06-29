import { apiClient } from '../../../utils/apiClient';

const BASE = '/api/v1/game/quiz-who/duel';

export interface QWBoardItem {
  id: string;
  title: string;
  image: string | null;
}
export interface QWLastAnswer {
  by: number;
  label: string;
  answer: string;
}
export interface QWDuelState {
  room_code: string;
  media_type: string;
  difficulty: string;
  board: QWBoardItem[];
  questions: { attr: string; label: string }[];
  your_player: number;
  your_secret_id: string;
  your_secret_title: string | null;
  your_eliminated: string[];
  opponent_joined: boolean;
  your_turn: boolean;
  last_answer: QWLastAnswer | null;
  finished: boolean;
  winner: number | null;
  you_won: boolean;
  player1: string;
  player2: string | null;
}

export const quizWhoDuelService = {
  create: (mediaType: string, difficulty: string): Promise<QWDuelState> =>
    apiClient(`${BASE}/create/`, {
      method: 'POST',
      body: JSON.stringify({ media_type: mediaType, difficulty }),
    }) as Promise<QWDuelState>,

  join: (roomCode: string): Promise<QWDuelState> =>
    apiClient(`${BASE}/join/`, {
      method: 'POST',
      body: JSON.stringify({ room_code: roomCode }),
    }) as Promise<QWDuelState>,

  state: (roomCode: string): Promise<QWDuelState> =>
    apiClient(`${BASE}/state/${roomCode}/`, { skipToast: true }) as Promise<QWDuelState>,

  ask: (roomCode: string, attribute: string): Promise<{ answer: string; eliminated: string[] }> =>
    apiClient(`${BASE}/ask/`, {
      method: 'POST',
      body: JSON.stringify({ room_code: roomCode, attribute }),
    }) as Promise<{ answer: string; eliminated: string[] }>,

  guess: (
    roomCode: string,
    guessId: string,
  ): Promise<{ correct: boolean; finished: boolean; winner?: number; secret_title?: string }> =>
    apiClient(`${BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ room_code: roomCode, guess_id: guessId }),
    }) as Promise<{ correct: boolean; finished: boolean; winner?: number; secret_title?: string }>,
};
