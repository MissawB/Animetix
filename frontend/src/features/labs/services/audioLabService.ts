import { AudioLabState, VoiceProfile } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/labs/audio';

export interface AudioProcessPayload {
  media_id: string;
  source_lang: string;
  target_lang: string;
}

export interface IngestVoicePayload {
  name: string;
  language: string;
  query: string;
  definition?: string;
  roles?: string;
}

export const audioLabService = {
  getState: async (): Promise<AudioLabState> => {
    return apiClient(`${API_BASE}/`);
  },
  process: async (data: AudioProcessPayload): Promise<AudioLabState> => {
    return apiClient(`${API_BASE}/process/`, { method: 'POST', body: JSON.stringify(data) });
  },
  searchSeiyuu: async (
    query: string,
    language?: string,
    origin?: string
  ): Promise<{ query: string; results: VoiceProfile[] }> => {
    let url = `${API_BASE}/seiyuu/?q=${encodeURIComponent(query)}`;
    if (language) url += `&language=${language}`;
    if (origin) url += `&origin=${origin}`;
    return apiClient(url);
  },
  ingestVoice: async (payload: IngestVoicePayload): Promise<{ message: string; profile: VoiceProfile }> => {
    return apiClient(`${API_BASE}/seiyuu/ingest/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

