import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export const useAdminEval = () => {
  const { data, isLoading: loading } = useQuery({
    queryKey: ['admin-eval-data'],
    queryFn: () => apiClient('/api/v1/admin/ai_eval/data/'),
    refetchOnWindowFocus: false,
  });

  return { data, loading };
};
