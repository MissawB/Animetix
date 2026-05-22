import React, { Component, ErrorInfo, ReactNode } from 'react';

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
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 p-6">
          <div className="bg-red-500/10 border-2 border-red-500 rounded-3xl p-10 max-w-2xl text-center">
            <h1 className="text-4xl font-black text-red-500 mb-6">CRITICAL FAILURE</h1>
            <p className="text-white text-lg opacity-80 mb-8">
              Une erreur inattendue s'est produite lors du rendu de l'interface.
            </p>
            <div className="bg-black/50 p-4 rounded-xl text-left overflow-auto max-h-40 mb-8 font-mono text-sm text-red-300">
                {this.state.error?.message}
            </div>
            <button
              className="bg-red-500 hover:bg-red-600 text-white font-black py-4 px-8 rounded-full transition-transform hover:scale-105"
              onClick={() => window.location.reload()}
            >
              REDÉMARRER LE SYSTÈME
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
