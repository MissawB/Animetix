import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRouter from './components/AppRouter'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { ToastContainer } from './components/ui/ToastContainer'
import { initObservability } from './utils/observability'
import './i18n/config'

// Initialisation de Sentry et PostHog
initObservability();

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <ErrorBoundary>
        <AppRouter />
        <ToastContainer />
      </ErrorBoundary>
    </StrictMode>,
  );
}
