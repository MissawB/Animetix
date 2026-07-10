import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../utils/apiClient';
import { useAuthStore } from '../store/authStore';
import MaintenancePage from '../pages/utils/MaintenancePage';
import type { AppConfig } from '../types';

/**
 * Garde globale du mode maintenance.
 *
 * Quand /api/v1/config/ annonce maintenance_mode, les visiteurs voient la
 * MaintenancePage à la place de l'app ; le staff garde l'app avec un bandeau.
 * Le poll (30 s) n'est actif que pendant la maintenance — la sortie se fait
 * donc sans F5. L'événement `animetix:maintenance` (émis par apiClient sur un
 * 503 {maintenance:true}) force une re-vérification immédiate en cours de
 * session.
 */
export const MaintenanceGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  const { data, refetch } = useQuery<Partial<AppConfig>>({
    queryKey: ['app-config'],
    queryFn: () => apiClient('/api/v1/config/', { skipToast: true }),
    staleTime: 60_000,
    retry: false,
    refetchOnWindowFocus: false,
    refetchInterval: (query) => (query.state.data?.maintenance_mode ? 30_000 : false),
  });

  React.useEffect(() => {
    const onMaintenance = () => {
      refetch();
    };
    window.addEventListener('animetix:maintenance', onMaintenance);
    return () => window.removeEventListener('animetix:maintenance', onMaintenance);
  }, [refetch]);

  // Config indisponible ou mode OFF : l'app fonctionne normalement (fail-open —
  // la maintenance est un état déclaré, jamais un effet de bord d'une panne).
  if (!data?.maintenance_mode) return <>{children}</>;

  if (user?.is_staff) {
    return (
      <>
        <div className="fixed top-0 inset-x-0 z-[5000] bg-yellow-400 text-black text-center text-[11px] font-black uppercase tracking-widest py-1.5 shadow-lg">
          {t(
            'maintenance.staff_banner',
            'Mode maintenance actif — seuls les admins voient le site',
          )}
        </div>
        {children}
      </>
    );
  }

  return (
    <MaintenancePage
      message={data.maintenance_message}
      until={data.maintenance_until}
      onRetry={() => refetch()}
    />
  );
};
