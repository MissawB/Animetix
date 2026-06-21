import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { audioLabService } from '../services/audioLabService';

export const useAudioLab = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['audiolab-state'];

  const { data, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => audioLabService.getState(),
    refetchOnWindowFocus: false,
  });

  const processMutation = useMutation({
    mutationFn: audioLabService.process,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  const seiyuuSearchMutation = useMutation({
    mutationFn: ({ q, language, origin }: { q: string; language?: string; origin?: string }) =>
      audioLabService.searchSeiyuu(q, language, origin),
  });

  const ingestVoiceMutation = useMutation({
    mutationFn: audioLabService.ingestVoice,
  });

  return {
    data,
    loading,
    processAudio: processMutation.mutateAsync,
    searchSeiyuu: (q: string, language?: string, origin?: string) =>
      seiyuuSearchMutation.mutateAsync({ q, language, origin }),
    ingestVoice: ingestVoiceMutation.mutateAsync,
    seiyuuResults: seiyuuSearchMutation.data?.results || [],
    isSearchingSeiyuu: seiyuuSearchMutation.isPending,
    isIngestingVoice: ingestVoiceMutation.isPending,
  };
};

