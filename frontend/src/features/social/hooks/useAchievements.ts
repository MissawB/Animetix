import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';

export const useAchievements = () => {
  return useQuery({
    queryKey: ['achievements'],
    queryFn: () => apiClient('/api/v1/achievements/'),
  });
};
