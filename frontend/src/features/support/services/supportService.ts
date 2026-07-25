import { apiClient } from '../../../utils/apiClient';
import type { SupportTicket } from '../../../types/admin';

export const supportService = {
  getTickets: async (): Promise<SupportTicket[]> => {
    return apiClient('/api/v1/support/tickets/');
  },

  createTicket: async (payload: { subject: string; query: string }): Promise<SupportTicket> => {
    return apiClient('/api/v1/support/tickets/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  rateTicket: async (id: number, score: number): Promise<SupportTicket> => {
    return apiClient(`/api/v1/support/tickets/${id}/rate/`, {
      method: 'PATCH',
      body: JSON.stringify({ score }),
    });
  },
};
