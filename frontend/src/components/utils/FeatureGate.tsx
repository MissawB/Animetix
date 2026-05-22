import React, { ReactNode } from 'react';
import { useFeatureFlag } from '../../hooks/useFeatureFlag';

interface FeatureGateProps {
  flag: string;
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Composant pour afficher du contenu conditionnellement basé sur un Feature Flag
 */
export const FeatureGate: React.FC<FeatureGateProps> = ({ flag, children, fallback = null }) => {
  const isEnabled = useFeatureFlag(flag);

  if (isEnabled === undefined) {
    // Facultatif: afficher un skeleton ou rien pendant le chargement des flags
    return null;
  }

  return isEnabled ? <>{children}</> : <>{fallback}</>;
};
