import { useQuery } from '@tanstack/react-query';
import { adminService } from '../services/adminService';

export const useHealth = () => {
  return useQuery({
    queryKey: ['health-status'],
    queryFn: adminService.getHealth,
    refetchInterval: 30000, // Rafraîchir toutes les 30s
  });
};

// Santé temps réel du cluster (GPU / inférence / Neo4j). Remplace un
// setInterval + useState maison dans ClusterHealthPanel : react-query gère le
// polling (15s), le cache, la dédup et le retry.
export const useClusterHealth = () => {
  return useQuery({
    queryKey: ['cluster-health'],
    queryFn: adminService.getClusterHealth,
    refetchInterval: 15000,
  });
};
