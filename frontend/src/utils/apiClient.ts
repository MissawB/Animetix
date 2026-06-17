import { useToastStore } from '../store/toastStore';
import { usePersonalizationStore } from '../store/personalizationStore';
import { auth } from './firebase';

export const apiClient = async (url: string, options: RequestInit & { skipToast?: boolean; isFormData?: boolean } = {}) => {
  const { skipToast, isFormData, ...fetchOptions } = options;
  const defaultHeaders: Record<string, string> = {
    'X-Requested-With': 'XMLHttpRequest',
  };

  if (!isFormData) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  // Inject Firebase Auth Token if available
  const firebaseUser = auth.currentUser;
  if (firebaseUser) {
    try {
      const token = await firebaseUser.getIdToken();
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    } catch (err) {
      console.error('Failed to get Firebase ID Token', err);
    }
  }

  // Récupération du CSRF Token
  const match = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
  if (match) {
    (defaultHeaders as Record<string, string>)['X-CSRFToken'] = match[2];
  }

  const config: RequestInit = {
    ...fetchOptions,
    headers: { ...defaultHeaders, ...fetchOptions.headers },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const errorMessage = errorData?.message || `Erreur ${response.status}: Impossible de récupérer les données.`;
      
      // Déclenchement global du Toast
      if (!skipToast) {
        useToastStore.getState().addToast(errorMessage, 'error');
      }
      
      throw new Error(errorMessage);
    }

    // Gérer les retours 204 No Content
    if (response.status === 204) return null;

    const data = await response.json();

    // Personalization Interceptor
    const visualConfig = data?.meta?.visual_config;
    if (visualConfig) {
      usePersonalizationStore.getState().updateConfig(visualConfig);
    }

    return data;
  } catch (error) {
    const err = error as Error;
    if (err.name === 'TypeError') {
      // Erreur de réseau (API injoignable, CORS, etc.)
      if (!skipToast) {
        useToastStore.getState().addToast('Serveur injoignable. Vérifiez votre connexion.', 'error');
      }
    }
    throw error;
  }
};
