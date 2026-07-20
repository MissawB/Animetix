import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export type MediaCharacter = { id: string; name: string; image?: string | null };

export const useMediaCharacters = (mediaType?: string, itemId?: string) =>
  useQuery<{ characters: MediaCharacter[] }>({
    queryKey: ['media-characters', mediaType, itemId],
    queryFn: () => apiClient(`/api/v1/media/${mediaType}/${itemId}/characters/`),
    enabled: !!mediaType && !!itemId,
  });
