import { useQuery } from '@tanstack/react-query';
import { socialService } from '../services/socialService';

export const useProfile = (username: string | undefined) => {
  return useQuery({
    queryKey: ['profile', username],
    queryFn: () => socialService.getProfile(username || ''),
    enabled: !!username,
  });
};
