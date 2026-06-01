import React, { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { usePersonalizationStore } from '../store/personalizationStore';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const checkAuth = useAuthStore((state) => state.checkAuth);
  const fetchPersonalizationSettings = usePersonalizationStore((state) => state.fetchSettings);

  useEffect(() => {
    checkAuth().then(() => {
      if (useAuthStore.getState().isAuthenticated) {
        fetchPersonalizationSettings();
      }
    });
  }, [checkAuth, fetchPersonalizationSettings]);

  return <>{children}</>;
};
