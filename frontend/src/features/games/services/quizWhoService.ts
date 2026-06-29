import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/quiz-who';

export interface QuizWhoCandidate {
  id: string;
  title: string;
  image: string | null;
}
export interface QuizWhoQuestion {
  attr: string;
  label: string;
}
export interface QuizWhoStart {
  media_type: string;
  board: QuizWhoCandidate[];
  questions: QuizWhoQuestion[];
  asked_count: number;
  game_over: boolean;
}
export interface QuizWhoAsk {
  answer: 'OUI' | 'NON';
  eliminated: string[];
  remaining_count: number;
  asked_count: number;
}
export interface QuizWhoGuess {
  correct: boolean;
  game_over: boolean;
  secret_title?: string;
  eliminated?: string[];
}

export const quizWhoService = {
  start: (mediaType?: string): Promise<QuizWhoStart> =>
    apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify(mediaType ? { media_type: mediaType } : {}),
    }) as Promise<QuizWhoStart>,

  ask: (attribute: string): Promise<QuizWhoAsk> =>
    apiClient(`${API_BASE}/ask/`, {
      method: 'POST',
      body: JSON.stringify({ attribute }),
    }) as Promise<QuizWhoAsk>,

  guess: (id: string): Promise<QuizWhoGuess> =>
    apiClient(`${API_BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ guess_id: id }),
    }) as Promise<QuizWhoGuess>,
};
