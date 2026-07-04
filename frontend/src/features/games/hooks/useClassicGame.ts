import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classicGameService } from '../services/classicService';
import type { ClassicGameState, ClassicHintKey } from '../../../types';

interface StartArgs {
  mediaType?: string;
  difficulty?: string;
  hintConfig?: ClassicHintKey[];
}

// Clé partagée : toute page qui démarre une partie via classicGameService.start
// (lobby, défi du jour) doit seeder ce cache, sinon la page de jeu ré-affiche
// la partie précédente encore « fraîche » (staleTime global de 5 min, persisté).
export const CLASSIC_STATE_QUERY_KEY = ['classic-state'];

export const useClassicGame = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = CLASSIC_STATE_QUERY_KEY;

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

  // Démarre une partie avec une configuration précise (univers, difficulté,
  // indices) — utilisé pour rejouer les mêmes réglages depuis l'écran de victoire.
  const startMutation = useMutation({
    mutationFn: ({ mediaType, difficulty, hintConfig }: StartArgs) =>
      classicGameService.start(mediaType, difficulty, hintConfig),
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  // Révèle un indice : on fusionne seulement le bloc `hints` renvoyé dans l'état
  // courant (le reste de la partie — tentatives, etc. — reste intact).
  const revealMutation = useMutation({
    mutationFn: classicGameService.reveal,
    onSuccess: (data) => {
      queryClient.setQueryData<ClassicGameState | undefined>(QUERY_KEY, (prev) =>
        prev ? { ...prev, hints: data.hints } : prev
      );
    },
  });

  // Rejoue une nouvelle partie : on ré-exécute la queryFn (comme le ferait un
  // remount) au lieu d'un window.location.reload() qui rechargeait toute l'app.
  const restart = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
    isGuessing: guessMutation.isPending,
    revealHint: revealMutation.mutateAsync,
    revealingHint: revealMutation.isPending,
    startGame: startMutation.mutateAsync,
    starting: startMutation.isPending,
    restart,
  };
};
