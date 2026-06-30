import { ClassicGameState, ClassicHints, ClassicHintKey } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/classic';

export interface ClassicGuessRequest {
  guess: string;
}

export interface ClassicRevealResponse {
  revealed_hints: string[];
  hints: ClassicHints;
}

export const classicGameService = {
  getState: async (): Promise<ClassicGameState> => {
    // Probe : un 400 signifie « aucune partie en cours » et est rattrapé par le
    // hook qui lance alors start(). On évite le toast d'erreur global trompeur.
    return apiClient(`${API_BASE}/state/`, { skipToast: true });
  },
  
  start: async (
    mediaType = 'Anime',
    difficulty = 'Normal',
    hintConfig?: ClassicHintKey[],
    daily = false,
    dailyDate?: string,
  ): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify({
        media_type: mediaType,
        difficulty,
        ...(hintConfig ? { hint_config: hintConfig } : {}),
        ...(daily ? { daily: true } : {}),
        ...(daily && dailyDate ? { daily_date: dailyDate } : {}),
      }),
    });
  },
  
  submit: async (data: ClassicGuessRequest): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  },

  // Titres du catalogue pour l'autocomplete (même catalogue que la validation).
  getTitles: async (): Promise<string[]> => {
    const data = (await apiClient(`${API_BASE}/titles/`, { skipToast: true })) as { titles?: string[] };
    return data?.titles ?? [];
  },

  reveal: async (hintType: ClassicHintKey): Promise<ClassicRevealResponse> => {
    return apiClient(`${API_BASE}/reveal/`, {
      method: 'POST',
      body: JSON.stringify({ hint_type: hintType }),
    });
  },
};
