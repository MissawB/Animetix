import { apiClient } from '../../../utils/apiClient';

export interface FusionRequest {
  title_A?: string;
  title_B?: string;
  media_type_A?: string;
  media_type_B?: string;
  chaos_level?: number;
  universe_balance?: number;
  art_style?: string;
  parent_id?: number;
}

export interface FusionResponse {
  fusion_id: number;
  task_id: string;
  title_a: string;
  title_b: string;
  item_a_image?: string;
  item_b_image?: string;
}

export interface FusionStatus {
  state: string;
  status: string;
  completed?: boolean;
  scenario?: string;
  image_url?: string;
}

export const forgeService = {
  startFusion: async (params: FusionRequest): Promise<FusionResponse> => {
    return apiClient('/api/v1/archetypist/start/', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  getFusionStatus: async (taskId: string, fusionId: number): Promise<FusionStatus> => {
    return apiClient(`/api/v1/archetypist/status/?task_id=${taskId}&fusion_id=${fusionId}`);
  },
};
