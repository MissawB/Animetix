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
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
  };
};

