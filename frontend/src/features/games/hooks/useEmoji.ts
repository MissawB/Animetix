import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { emojiService } from '../services/emojiService';

export const useEmoji = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['emoji-state'];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => emojiService.getState(),
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation({
    mutationFn: emojiService.submit,
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
