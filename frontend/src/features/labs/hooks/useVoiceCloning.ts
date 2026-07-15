import { useMutation } from '@tanstack/react-query';
import { labService } from '../services/labService';

export const useVoiceCloning = () => {
  const mutation = useMutation({
    mutationFn: ({ text, audioFile, pitch }: { text: string; audioFile: File; pitch: number }) =>
      labService.cloneVoice(text, audioFile, pitch),
  });

  return {
    clone: mutation.mutateAsync,
    loading: mutation.isPending,
    result: mutation.data,
    error: mutation.error,
  };
};
