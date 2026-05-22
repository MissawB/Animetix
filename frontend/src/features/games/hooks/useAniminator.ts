import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { animinatorService } from '../services/animinatorService';

export const useAniminator = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['animinator-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => animinatorService.getState(),
    refetchOnWindowFocus: false,
  });

  const frameMutation = useMutation({
    mutationFn: animinatorService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleFrame: frameMutation.mutateAsync,
  };
};
