import { useMutation } from '@tanstack/react-query';
import { cloneVoice } from '../../../api';

export const useVoiceCloning = () => {
  const mutation = useMutation({
    mutationFn: ({ text, audioFile, pitch }: { text: string, audioFile: File, pitch: number }) => 
      cloneVoice(text, audioFile, pitch),
  });

  return {
    clone: mutation.mutateAsync,
    isLoading: mutation.isPending,
    result: mutation.data,
    error: mutation.error
  };
};
