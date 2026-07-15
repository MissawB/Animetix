import { useQuery } from '@tanstack/react-query';
import { socialService } from '../services/socialService';

export const useLeaderboard = () => {
  return useQuery({
    queryKey: ['leaderboard'],
    queryFn: socialService.getLeaderboard,
  });
};
