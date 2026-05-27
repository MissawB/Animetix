import { apiClient } from '../../../utils/apiClient';
import { CovertestState } from '../../../types';

const API_BASE = '/api/v1/game/covertest';

export interface CovertestGuessRequest {
  guess: string;
}

export const covertestService = {
  getState: async (): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: CovertestGuessRequest): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};

