import { useQuery } from '@tanstack/react-query';
import { mediaService } from '../services/mediaService';

export const useMediaDetail = (mediaType?: string, itemId?: string) => {
  return useQuery({
    queryKey: ['media-detail', mediaType, itemId],
    queryFn: () => mediaType && itemId ? mediaService.getDetail(mediaType, itemId) : Promise.reject('Missing params'),
    enabled: !!mediaType && !!itemId,
  });
};
