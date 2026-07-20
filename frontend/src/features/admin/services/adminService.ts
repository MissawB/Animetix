import { apiClient } from '../../../utils/apiClient';

export const adminService = {
  getEval: async () => apiClient('/api/v1/admin/eval/'),
  getHealth: async () => apiClient('/api/v1/admin/health/'),
  // skipToast: le panel affiche son propre état "cluster injoignable".
  getClusterHealth: async () => apiClient('/api/monitoring/cluster-health/', { skipToast: true }),
  getUsers: async () => apiClient('/api/v1/admin/users/'),
  toggleStaff: async (userId: number) =>
    apiClient(`/api/v1/admin/users/${userId}/toggle-staff/`, { method: 'POST' }),
  toggleActive: async (userId: number) =>
    apiClient(`/api/v1/admin/users/${userId}/toggle-active/`, { method: 'POST' }),
};
