import { ClassicGameState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/classic';

export interface ClassicGuessRequest {
  guess: string;
}

export const classicGameService = {
  getState: async (): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  
  start: async (mediaType = 'Anime', difficulty = 'Normal'): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify({ media_type: mediaType, difficulty }),
    });
  },
  
  submit: async (data: ClassicGuessRequest): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
