import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRouter from './components/AppRouter'
import { AuthProvider } from './context/AuthProvider'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { ToastContainer } from './components/ui/ToastContainer'
import { initObservability } from './utils/observability'
import './i18n/config'

// Initialisation de Sentry et PostHog
initObservability();

// Après un déploiement, les onglets déjà ouverts référencent d'anciens chunks
// hashés qui n'existent plus : l'import dynamique échoue et l'ErrorBoundary
// affiche CRITICAL FAILURE. On recharge une fois pour récupérer le nouvel
// index.html, avec une garde anti-boucle si l'asset est durablement absent.
window.addEventListener('vite:preloadError', (event) => {
  const lastReloadAt = Number(sessionStorage.getItem('chunk-reload-at') ?? 0);
  if (Date.now() - lastReloadAt > 30_000) {
    sessionStorage.setItem('chunk-reload-at', String(Date.now()));
    event.preventDefault();
    window.location.reload();
  }
});

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <ErrorBoundary>
        <AuthProvider>
          <AppRouter />
          <ToastContainer />
        </AuthProvider>
      </ErrorBoundary>
    </StrictMode>,
  );
}
