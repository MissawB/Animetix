import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paradoxService } from '../services/paradoxService';

export const useParadox = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['paradox-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => paradoxService.getState(),
    refetchOnWindowFocus: false,
  });

  const moveMutation = useMutation({
    mutationFn: paradoxService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleMove: moveMutation.mutateAsync,
  };
};
