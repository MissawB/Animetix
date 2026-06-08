import { useMutation } from '@tanstack/react-query';
import { labService } from '../services/labService';

export const useNeuralDiagnostics = () => {
  const { mutateAsync, isPending: loading, data, error } = useMutation({
    mutationFn: (prompt: string) => labService.runDiagnostics(prompt),
  });

  return {
    runDiagnostic: mutateAsync,
    loading,
    data,
    error,
  };
};
