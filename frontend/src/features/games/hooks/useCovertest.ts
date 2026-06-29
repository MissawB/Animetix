import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { covertestService, CovertestGuessRequest } from '../services/covertestService';
import { CovertestState } from '../../../types';

export const useCovertest = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['covertest-state'];

  const { data: gameState, isLoading: loading } = useQuery<CovertestState>({
    queryKey: QUERY_KEY,
    queryFn: () => covertestService.getState(),
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation<CovertestState, Error, CovertestGuessRequest>({
    mutationFn: covertestService.submit,
    onSuccess: (newState) => {
      // The guess endpoint only returns the round's progress (guesses, game_over…),
      // NOT the cover fields. Merge so cover_url/locale/volume/author survive a guess
      // instead of being wiped (which blanked the cover after the first attempt).
      queryClient.setQueryData<CovertestState | undefined>(QUERY_KEY, (prev) =>
        prev ? { ...prev, ...newState } : newState
      );
    },
  });

  // Démarre une nouvelle couverture (manche suivante / nouvelle session).
  const startMutation = useMutation<CovertestState, Error, { isDaily?: boolean; origin?: string } | void>({
    mutationFn: (opts) => covertestService.start(!!opts?.isDaily, opts?.origin),
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  // Révèle la réponse (défaite / abandon) en fusionnant l'état renvoyé.
  const revealMutation = useMutation<CovertestState, Error, void>({
    mutationFn: () => covertestService.reveal(),
    onSuccess: (data) => {
      queryClient.setQueryData<CovertestState | undefined>(QUERY_KEY, (prev) =>
        prev ? { ...prev, ...data } : data
      );
    },
  });

  // Rejoue : ré-exécute la queryFn (équivalent d'un remount) sans recharger l'app.
  const restart = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
    isGuessing: guessMutation.isPending,
    startGame: startMutation.mutateAsync,
    starting: startMutation.isPending,
    revealAnswer: revealMutation.mutateAsync,
    restart,
  };
};
