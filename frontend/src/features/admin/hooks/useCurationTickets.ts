import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export interface CurationTicket {
  id: number;
  item_title: string;
  issue_description: string;
  source_pg: any;
  source_neo4j: any;
  is_resolved: boolean;
  created_at: string;
}

export const useCurationTickets = () => {
  const queryClient = useQueryClient();

  const ticketsQuery = useQuery({
    queryKey: ['admin', 'curation', 'tickets'],
    queryFn: async () => apiClient('/api/v1/curation/')
  });

  const statsQuery = useQuery({
    queryKey: ['admin', 'curation', 'stats'],
    queryFn: async () => apiClient('/api/v1/curation/stats/')
  });

  const resolveMutation = useMutation({
    mutationFn: async (id: number) => apiClient(`/api/v1/curation/${id}/resolve/`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'curation'] });
    }
  });

  return {
    tickets: ticketsQuery.data?.results || [],
    isLoading: ticketsQuery.isLoading,
    stats: statsQuery.data,
    resolve: resolveMutation.mutate,
    isResolving: resolveMutation.isPending
  };
};
