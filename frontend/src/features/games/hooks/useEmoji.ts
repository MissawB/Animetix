import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { emojiService, EmojiGuessRequest } from '../services/emojiService';
import { EmojiState } from '../../../types';

export const useEmoji = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['emoji-state'];

  const { data: gameState, isLoading: loading } = useQuery<EmojiState>({
    queryKey: QUERY_KEY,
    queryFn: () => emojiService.getState(),
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation<EmojiState, Error, EmojiGuessRequest>({
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

