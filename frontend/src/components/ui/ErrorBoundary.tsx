import React, { Component, ErrorInfo, ReactNode } from 'react';
import * as Sentry from '@sentry/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    // Reporte le crash de rendu à Sentry avec la pile de composants React.
    Sentry.captureException(error, {
      contexts: { react: { componentStack: errorInfo.componentStack } },
    });
  }

  public render() {
    if (this.state.hasError) {
      // Volontairement auto-suffisant (pas d'i18n, de router ni de composants
      // partagés : ils peuvent être la cause du crash) — mais aligné sur
      // l'univers visuel des pages d'erreur (ErrorPageShell).
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#05050a] text-white p-6">
          <div className="text-center space-y-8 max-w-xl">
            <div className="relative inline-block">
              <div className="absolute -inset-8 bg-red-500/10 rounded-full blur-3xl animate-pulse" />
              <div className="relative w-32 h-32 bg-gradient-to-br from-red-500 to-rose-600 rounded-[2rem] flex items-center justify-center rotate-12 shadow-2xl mx-auto">
                <span className="text-6xl font-black text-black select-none">!</span>
              </div>
            </div>

            <h1 className="text-[7rem] leading-none font-black italic manga-font tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white/20 to-white/5 select-none">
              CRASH
            </h1>

            <div className="space-y-3">
              <h2 className="text-3xl font-black italic manga-font uppercase tracking-tight">
                Erreur <span className="text-red-500 text-glow">critique</span>
              </h2>
              <p className="text-sm font-bold text-gray-400 uppercase tracking-[0.2em] max-w-md mx-auto">
                Une erreur inattendue s'est produite lors du rendu de l'interface.
              </p>
            </div>

            <div className="bg-white/5 border border-red-500/20 p-4 rounded-2xl text-left overflow-auto max-h-40 font-mono text-sm text-red-300">
              {this.state.error?.message}
            </div>

            <button
              className="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-black py-4 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all font-black uppercase italic tracking-wider"
              onClick={() => window.location.reload()}
            >
              Redémarrer le système
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
