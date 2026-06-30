import { useQuery } from '@tanstack/react-query';
import { utilsService } from '../services/utilsService';

export const useDailyChallenge = (date?: string) => {
  return useQuery({
    queryKey: ['daily-challenge', date ?? 'today'],
    queryFn: () => utilsService.getDaily(date),
  });
};
