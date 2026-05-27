import { ParadoxState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/paradox';

export interface ParadoxGuessRequest {
  intruder_id: number;
}

export const paradoxService = {
  getState: async (): Promise<ParadoxState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: ParadoxGuessRequest): Promise<ParadoxState> => {
    return apiClient(`${API_BASE}/move/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
