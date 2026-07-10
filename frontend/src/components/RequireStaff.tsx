import React from 'react';
import { Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import ForbiddenPage from '../pages/utils/ForbiddenPage';

/**
 * Route-gabarit qui réserve son sous-arbre aux comptes staff.
 *
 * Le backend 403 déjà toutes les API admin ; cette garde évite simplement de
 * rendre des dashboards vides aux non-staff en affichant la page 403 dédiée.
 * Pendant la résolution de session (isLoading), on n'affiche rien plutôt
 * qu'un flash de page interdite.
 */
export const RequireStaff: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);

  if (isLoading) return null;
  if (!user?.is_staff) return <ForbiddenPage />;
  return <Outlet />;
};
