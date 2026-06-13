import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/codemanga';

export interface CodeMangaPlayer {
  id: string | number;
  username: string;
  is_online: boolean;
}

export interface CodeMangaState {
  room_code: string;
  players: CodeMangaPlayer[];
  current_code?: string;
  is_game_over: boolean;
}

export interface CodeMangaAction {
  type: string;
  [key: string]: unknown;
}

export const codemangaService = {
  getState: async (code: string): Promise<CodeMangaState> => {
    return apiClient(`${API_BASE}/room/${code}`);
  },
  submit: async (data: CodeMangaAction): Promise<CodeMangaState> => {
    return apiClient(`${API_BASE}/action/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
