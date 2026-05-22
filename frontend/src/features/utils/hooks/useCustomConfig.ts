import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { utilsService } from '../services/utilsService';
import { useToastStore } from '../../../store/toastStore';

export const useCustomConfig = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToastStore();

  const query = useQuery({
    queryKey: ['custom-config'],
    queryFn: utilsService.getConfig,
  });

  const mutation = useMutation({
    mutationFn: async (newConfig: any) => {
        // En un vrai projet, utilsService aurait une méthode updateConfig
        return fetch('/api/v1/custom-config/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom-config'] });
      addToast('Paramètres enregistrés !', 'success');
    },
  });

  return {
    config: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    saveConfig: mutation.mutate,
    isSaving: mutation.isPending,
  };
};
