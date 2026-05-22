import { useState, useEffect } from 'react';
import posthog from 'posthog-js';

/**
 * Hook pour vérifier l'état d'un Feature Flag PostHog
 */
export const useFeatureFlag = (flagName: string) => {
  const [isEnabled, setIsEnabled] = useState<boolean | undefined>(
    posthog.isFeatureEnabled(flagName)
  );

  useEffect(() => {
    // Callback quand les flags sont chargés ou mis à jour
    const handleFlagsUpdated = () => {
      setIsEnabled(posthog.isFeatureEnabled(flagName));
    };

    posthog.onFeatureFlags(handleFlagsUpdated);

    // Nettoyage
    return () => {
      // PostHog ne propose pas de removeListener explicite simple ici, 
      // mais le callback ne posera pas de problème de fuite majeure.
    };
  }, [flagName]);

  return isEnabled;
};
