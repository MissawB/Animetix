import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { blindtestService } from '../services/blindtestService';

export const useBlindtest = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['blindtest-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      try {
        return await blindtestService.getState();
      } catch {
        return await blindtestService.startGame();
      }
    },
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation({
    mutationFn: blindtestService.submitGuess,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  const restartMutation = useMutation({
    mutationFn: blindtestService.startGame,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return { 
    gameState, 
    loading, 
    handleGuess: guessMutation.mutateAsync, 
    restartGame: restartMutation.mutate 
  };
};

