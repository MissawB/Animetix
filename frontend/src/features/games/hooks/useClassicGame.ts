import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ClassicGameState } from '../../../types';
import { classicGameService } from '../services/classicService';

export const useClassicGame = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['classic-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => classicGameService.getState(),
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation({
    mutationFn: classicGameService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
  };
};
