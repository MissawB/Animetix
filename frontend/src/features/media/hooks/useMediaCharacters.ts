import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export type MediaCharacter = { id: string; name: string; image?: string | null };

export const useMediaCharacters = (mediaType?: string, itemId?: string, limit?: number) =>
  useQuery<{ characters: MediaCharacter[]; total?: number }>({
    queryKey: ['media-characters', mediaType, itemId, limit ?? 'default'],
    queryFn: () =>
      apiClient(
        `/api/v1/media/${mediaType}/${itemId}/characters/${limit ? `?limit=${limit}` : ''}`,
      ),
    enabled: !!mediaType && !!itemId,
    // en passant de 18 -> tout, on garde la grille affichée pendant le chargement
    placeholderData: keepPreviousData,
  });
