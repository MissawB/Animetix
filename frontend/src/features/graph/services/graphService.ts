import { GraphData } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

export const graphService = {
  getGraphNeighborhood: async (id: string, type: string, depth: number = 1): Promise<GraphData> => {
    return apiClient(`/api/v1/graph/neighbors/?id=${id}&type=${type}&depth=${depth}`);
  },
};
