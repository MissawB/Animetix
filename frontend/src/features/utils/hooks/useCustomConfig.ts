import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { utilsService } from '../services/utilsService';
import { useToastStore } from '../../../store/toastStore';
import { useAuthStore } from '../../../store/authStore';
import { UserConfig } from '../../../types';

export const useCustomConfig = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToastStore();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const query = useQuery({
    queryKey: ['custom-config'],
    queryFn: utilsService.getConfig,
    enabled: isAuthenticated,
  });

  const mutation = useMutation({
    mutationFn: async (newConfig: Partial<UserConfig>) => {
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
