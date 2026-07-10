import { useToastStore } from '../store/toastStore';
import { usePersonalizationStore } from '../store/personalizationStore';
import { auth } from './firebase';

export const apiClient = async (
  url: string,
  options: RequestInit & {
    skipToast?: boolean;
    isFormData?: boolean;
    responseType?: 'json' | 'blob';
  } = {},
) => {
  const { skipToast, isFormData, responseType = 'json', ...fetchOptions } = options;
  const defaultHeaders: Record<string, string> = {
    'X-Requested-With': 'XMLHttpRequest',
  };

  if (!isFormData && responseType === 'json') {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  // Inject Firebase Auth Token if available. `auth` is exported as non-null for
  // compile-time convenience but is genuinely null at runtime when the Firebase
  // config is absent (e.g. CI/e2e, where firebase.googleapis.com is blocked), so
  // guard it — otherwise every apiClient call throws and AllowAny features (e.g.
  // akinetix classic) crash for unauthenticated users.
  const firebaseUser = auth?.currentUser;
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
      // DRF surfaces errors as `detail`; our views use `error`/`message`.
      const errorMessage =
        errorData?.message ||
        errorData?.error ||
        errorData?.detail ||
        `Erreur ${response.status}: Impossible de récupérer les données.`;

      // 503 {maintenance:true} : le middleware backend annonce le mode
      // maintenance — on notifie la garde globale (bascule immédiate) et on
      // n'affiche pas de toast (la page dédiée prend le relais).
      const isMaintenance = response.status === 503 && errorData?.maintenance === true;
      if (isMaintenance) {
        window.dispatchEvent(new CustomEvent('animetix:maintenance'));
      }

      // Déclenchement global du Toast
      if (!skipToast && !isMaintenance) {
        useToastStore.getState().addToast(errorMessage, 'error');
      }

      // On attache le code HTTP à l'erreur pour permettre une gestion fine en aval
      // (ex. ne pas retenter les 4xx dans React Query).
      const error = new Error(errorMessage) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }

    // Gérer les retours 204 No Content
    if (response.status === 204) return null;

    if (responseType === 'blob') {
      return response.blob();
    }

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
        useToastStore
          .getState()
          .addToast('Serveur injoignable. Vérifiez votre connexion.', 'error');
      }
    }
    throw error;
  }
};
