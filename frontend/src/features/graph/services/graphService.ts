import { GraphData } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

export const graphService = {
  getGraphNeighborhood: async (id: string, type: string, depth: number = 1): Promise<GraphData> => {
    return apiClient(`/api/v1/graph/neighbors/?id=${id}&type=${type}&depth=${depth}`);
  },
  getDebugger: async () => apiClient('/api/v1/graph/debugger/'),
  postDebugger: async (data: Record<string, unknown>) =>
    apiClient('/api/v1/graph/debugger/', { method: 'POST', body: JSON.stringify(data) }),
  getLoreMap: async () => apiClient('/api/v1/graph/lore-map/'),
};
