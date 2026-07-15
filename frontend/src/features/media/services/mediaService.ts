import { apiClient } from '../../../utils/apiClient';

export const mediaService = {
  getDetail: async (mediaType: string, itemId: string) => {
    return apiClient(`/api/v1/media/${mediaType}/${itemId}/`);
  },

  syncMangaProgress: async (
    mediaId: string,
    chapterNumber: string,
  ): Promise<{
    success: boolean;
    results: Record<string, { success: boolean; error?: string }>;
  }> => {
    return apiClient(`/api/v1/media/Manga/${mediaId}/chapters/${chapterNumber}/sync/`, {
      method: 'POST',
    });
  },
};
