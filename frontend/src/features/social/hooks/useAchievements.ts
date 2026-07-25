import { useQuery } from '@tanstack/react-query';
import { socialService } from '../services/socialService';

export const useAchievements = () => {
  return useQuery({
    queryKey: ['achievements'],
    queryFn: async () => {
      const data = await socialService.getAchievements();
      return data.results || data;
    },
  });
};
