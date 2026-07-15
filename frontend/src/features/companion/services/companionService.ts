import { apiClient } from '../../../utils/apiClient';

export interface CompanionResponse {
  response: string;
  history: { role: string; content: string }[];
}

export const companionService = {
  interact: async (
    mentorId: string,
    message: string,
    contextUrl = '',
    customPersona?: string,
  ): Promise<CompanionResponse> => {
    return apiClient('/api/v1/companion/interact/', {
      method: 'POST',
      body: JSON.stringify({
        mentor_id: mentorId,
        user_message: message,
        context_url: contextUrl,
        custom_persona: customPersona,
      }),
    });
  },
};
