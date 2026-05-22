import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { codemangaService } from '../services/codemangaService';

export const useCodeManga = (code: string) => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['codemanga', code];

  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => codemangaService.getState(code),
    refetchOnWindowFocus: false,
  });

  const actionMutation = useMutation({
    mutationFn: codemangaService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleAction: actionMutation.mutateAsync,
  };
};
