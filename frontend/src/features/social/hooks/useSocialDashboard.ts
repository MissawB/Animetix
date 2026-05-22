import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { socialService } from '../services/socialService';

export const useSocialDashboard = () => {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['social-dashboard'],
    queryFn: socialService.getDashboard,
  });

  const toggleFollowMutation = useMutation({
    mutationFn: socialService.toggleFollow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-dashboard'] });
    }
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    toggleFollow: toggleFollowMutation.mutate
  };
};
