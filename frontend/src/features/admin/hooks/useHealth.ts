import { useQuery } from '@tanstack/react-query';
import { adminService } from '../services/adminService';

export const useHealth = () => {
  return useQuery({
    queryKey: ['health-status'],
    queryFn: adminService.getHealth,
    refetchInterval: 30000, // Rafraîchir toutes les 30s
  });
};
