import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';

// Stub Sentry so componentDidCatch does not reach the real SDK.
const captureExceptionMock = vi.fn();
vi.mock('@sentry/react', () => ({
  captureException: (...args: unknown[]) => captureExceptionMock(...args),
}));

import { ErrorBoundary } from '../ErrorBoundary';

function Boom({ message }: { message: string }): React.ReactElement {
  throw new Error(message);
}

describe('ErrorBoundary', () => {
  afterEach(() => {
    captureExceptionMock.mockClear();
  });

  it('renders children when nothing throws', () => {
    render(
      <ErrorBoundary>
        <p>Healthy content</p>
      </ErrorBoundary>,
    );
    expect(screen.getByText('Healthy content')).toBeInTheDocument();
    expect(captureExceptionMock).not.toHaveBeenCalled();
  });

  it('renders the fallback UI and the error message when a child throws', () => {
    // React logs the caught error to console.error during this render; silence it.
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom message="kaboom-from-child" />
      </ErrorBoundary>,
    );

    // Fallback restylé sur l'univers des pages d'erreur : « CRASH / Erreur critique ».
    expect(screen.getByText('CRASH')).toBeInTheDocument();
    expect(screen.getByText('kaboom-from-child')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Redémarrer le système/i })).toBeInTheDocument();

    // componentDidCatch should have reported to Sentry.
    expect(captureExceptionMock).toHaveBeenCalledTimes(1);
    expect(captureExceptionMock.mock.calls[0][0]).toBeInstanceOf(Error);

    consoleErrorSpy.mockRestore();
  });
});
