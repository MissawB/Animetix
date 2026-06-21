import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classicGameService } from '../services/classicService';

export const useClassicGame = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['classic-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      try {
        return await classicGameService.getState();
      } catch {
        return await classicGameService.start();
      }
    },
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation({
    mutationFn: classicGameService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  // Rejoue une nouvelle partie : on ré-exécute la queryFn (comme le ferait un
  // remount) au lieu d'un window.location.reload() qui rechargeait toute l'app.
  const restart = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
    restart,
  };
};
