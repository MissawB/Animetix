import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { emojiService, EmojiGuessRequest } from '../services/emojiService';
import { EmojiState } from '../../../types';

export const useEmoji = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['emoji-state'];

  // Flux piloté par le sélecteur : pas d'auto-start au montage (enabled:false).
  // On veut d'abord la page de choix (type d'œuvre + difficulté). L'état vient
  // ensuite des mutations start/guess/giveup qui écrivent dans le cache.
  const { data: gameState } = useQuery<EmojiState>({
    queryKey: QUERY_KEY,
    queryFn: () => emojiService.getState(),
    enabled: false,
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation<EmojiState, Error, EmojiGuessRequest>({
    mutationFn: emojiService.submit,
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

  const startMutation = useMutation<
    EmojiState,
    Error,
    { mediaType?: string; difficulty?: string }
  >({
    mutationFn: ({ mediaType, difficulty }) => emojiService.start(mediaType, difficulty),
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    starting: startMutation.isPending,
    handleGuess: guessMutation.mutateAsync,
    giveUp: () => giveUpMutation.mutate(),
    // Lance une partie avec le type d'œuvre + la difficulté choisis.
    start: (mediaType?: string, difficulty?: string) =>
      startMutation.mutate({ mediaType, difficulty }),
    // Revient à l'écran de choix (vide l'état courant). resetQueries repasse
    // l'observateur monté à "sans donnée" ; enabled:false ⇒ pas de refetch.
    reset: () => queryClient.resetQueries({ queryKey: QUERY_KEY }),
  };
};
