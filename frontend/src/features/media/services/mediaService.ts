import { apiClient } from '../../../utils/apiClient';

export const mediaService = {
  getDetail: async (mediaType: string, itemId: string) => {
    return apiClient(`/api/v1/media/${mediaType}/${itemId}/`);
  }
};
