import { useQuery } from '@tanstack/react-query';
import { utilsService } from '../services/utilsService';

export const useDailyChallenge = () => {
  return useQuery({
    queryKey: ['daily-challenge'],
    queryFn: utilsService.getDaily,
  });
};
