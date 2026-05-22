import { useQuery } from '@tanstack/react-query';
import { getProfile } from '../../../api';

export const useProfile = (username: string | undefined) => {
  return useQuery({
    queryKey: ['profile', username],
    queryFn: () => getProfile(username || ''),
    enabled: !!username,
  });
};
