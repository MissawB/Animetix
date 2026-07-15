import { MediaItem } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

export const searchService = {
  searchMedia: async (query: string, mediaType = 'anime'): Promise<MediaItem[]> => {
    return apiClient(`/api/v1/search/?q=${encodeURIComponent(query)}&media_type=${mediaType}`);
  },

  searchByImage: async (
    file: File,
    target: 'work' | 'character' = 'work',
  ): Promise<MediaItem[]> => {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('target', target);
    return apiClient('/api/v1/media/search/', { method: 'POST', body: formData, isFormData: true });
  },
};
