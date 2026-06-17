import { useQuery } from '@tanstack/react-query';

export const useAdminEval = () => {
  const { data, isLoading: loading } = useQuery({
    queryKey: ['admin-eval-data'],
    queryFn: async () => {
      const res = await fetch('/api/v1/admin/ai_eval/data/');
      return res.json();
    },
    refetchOnWindowFocus: false,
  });

  return { data, loading };
};
