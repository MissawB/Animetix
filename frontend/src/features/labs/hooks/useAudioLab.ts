import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AudioLabState } from '../../../types';
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

  return {
    data,
    loading,
    processAudio: processMutation.mutateAsync,
  };
};
