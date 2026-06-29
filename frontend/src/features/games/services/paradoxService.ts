import { ParadoxState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/paradox';

export interface ParadoxGuessRequest {
  intruder_id: number;
}

export const paradoxService = {
  getState: async (): Promise<ParadoxState> => {
    // 400 (no active game) is expected on first load — handled by the caller's
    // fallback start, so we don't want a raw toast here.
    return apiClient(`${API_BASE}/state/`, { skipToast: true });
  },
  submit: async (data: ParadoxGuessRequest): Promise<ParadoxState> => {
    return apiClient(`${API_BASE}/move/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
