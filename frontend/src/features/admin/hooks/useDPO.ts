import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export const useDPO = () => {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['dpo-feedbacks'],
    queryFn: () => apiClient('/api/v1/mlops/dpo/curation/'),
  });

  const mutation = useMutation({
    mutationFn: async (payload: { feedback_id: number; chosen_text: string }) => {
      return apiClient('/api/v1/mlops/dpo/curation/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dpo-feedbacks'] });
    },
  });

  return {
    feedbacks: query.data || [],
    isLoading: query.isLoading,
    curate: mutation.mutate,
    isSubmitting: mutation.isPending
  };
};
