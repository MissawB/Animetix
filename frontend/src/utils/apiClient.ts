import { useToastStore } from '../store/toastStore';
import { usePersonalizationStore } from '../store/personalizationStore';

export const apiClient = async (url: string, options: RequestInit & { skipToast?: boolean } = {}) => {
  const { skipToast, ...fetchOptions } = options;
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  };

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
  } catch (error: any) {
    if (error.name === 'TypeError') {
      // Erreur de réseau (API injoignable, CORS, etc.)
      if (!skipToast) {
        useToastStore.getState().addToast('Serveur injoignable. Vérifiez votre connexion.', 'error');
      }
    }
    throw error;
  }
};
