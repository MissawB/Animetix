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

  const startMutation = useMutation<EmojiState, Error, string | undefined>({
    mutationFn: (mediaType) => emojiService.start(mediaType),
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  const giveUpMutation = useMutation<EmojiState, Error, void>({
    mutationFn: () => emojiService.giveUp(),
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  // Rejoue : tire un nouveau secret (nouvelle séquence d'emojis) côté serveur.
  const restart = (mediaType?: string) => startMutation.mutate(mediaType);

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
    giveUp: () => giveUpMutation.mutate(),
    restart,
  };
};

