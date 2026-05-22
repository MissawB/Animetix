import { apiClient } from '../../../utils/apiClient';

export const labService = { 
  getLatent: async () => apiClient('/api/v1/lab/latent/'), 
  getManga: async () => apiClient('/api/v1/lab/manga/'), 
  getSpatial: async () => apiClient('/api/v1/lab/spatial/') 
};
