import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export type CharacterGraphNode = {
  id: string;
  name: string;
  image?: string | null;
  popularity: number;
};
export type CharacterGraphLink = { source: string; target: string };
export type CharacterGraphData = {
  nodes: CharacterGraphNode[];
  links: CharacterGraphLink[];
};

export const useCharacterGraph = (mediaType?: string, itemId?: string, enabled = true) =>
  useQuery<CharacterGraphData>({
    queryKey: ['media-characters-graph', mediaType, itemId],
    queryFn: () => apiClient(`/api/v1/media/${mediaType}/${itemId}/characters/graph/`),
    enabled: enabled && !!mediaType && !!itemId,
    staleTime: 5 * 60 * 1000,
  });
