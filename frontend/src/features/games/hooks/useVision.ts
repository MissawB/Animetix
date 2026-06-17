import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { visionService } from '../services/visionService';

export const useVision = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['vision-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      try {
        return await visionService.getState();
      } catch {
        return await visionService.startGame();
      }
    },
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation({
    mutationFn: visionService.submitGuess,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  const restartMutation = useMutation({
    mutationFn: visionService.startGame,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
    restartGame: restartMutation.mutateAsync
  };
};
