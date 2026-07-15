import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';

/** Shape of every SSE JSON event coming from the server. */
export interface SSEEvent {
  type: string;
  data?: unknown;
  content?: unknown;
  [key: string]: unknown;
}

export interface UseSSEOptions {
  /**
   * Full URL to the SSE endpoint (will be passed to `new EventSource(url)`).
   * Example: `/api/v1/stream/tot/?q=${encodeURIComponent(query)}`
   */
  url: string;

  /**
   * Called for every `onmessage` event after JSON.parse.
   * Return `'close'` from this handler to close the stream.
   */
  onEvent: (event: SSEEvent) => void | 'close';

  /**
   * If true, require authentication before opening the stream.
   * When the user is not logged-in, `error` will be set and the stream won't start.
   * @default true
   */
  requireAuth?: boolean;

  /** Custom message shown when the user is not authenticated. */
  authErrorMessage?: string;

  /** Custom message shown when the stream fails before any event is received (likely 402). */
  paymentErrorMessage?: string;
}

export interface UseSSEReturn {
  /** Start (or restart) the SSE stream. */
  start: () => void;
  /** Manually stop the stream. */
  stop: () => void;
  /** Whether the stream is currently open. */
  isStreaming: boolean;
  /** Error message (auth / payment / generic). */
  error: string | null;
  /** Discriminator for the error. */
  errorKind: 'auth' | 'payment' | 'generic' | null;
}

/**
 * Shared SSE hook — the EventSource equivalent of `useSocket.ts`.
 *
 * Encapsulates the full lifecycle:
 * - Auth guard (EventSource cannot read HTTP 401/402 status)
 * - Ref-based cleanup on unmount
 * - `receivedAny` heuristic for payment-related failures
 */
export function useSSE({
  url,
  onEvent,
  requireAuth = true,
  authErrorMessage = "Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi d'abord.",
  paymentErrorMessage = 'Requête refusée. Vérifie ton solde de Berrix (ce mode IA en consomme) puis réessaie.',
}: UseSSEOptions): UseSSEReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<'auth' | 'payment' | 'generic' | null>(null);

  const esRef = useRef<EventSource | null>(null);
  const receivedAnyRef = useRef(false);

  // Keep the latest callback in a ref so we don't re-create the EventSource
  // when only the handler identity changes.
  const onEventRef = useRef(onEvent);
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setIsStreaming(false);
  }, []);

  const start = useCallback(() => {
    // Auth guard — EventSource cannot read HTTP 401/402 status codes.
    if (requireAuth && !useAuthStore.getState().isAuthenticated) {
      setError(authErrorMessage);
      setErrorKind('auth');
      return;
    }

    // Close any previous stream.
    esRef.current?.close();
    setError(null);
    setErrorKind(null);
    receivedAnyRef.current = false;
    setIsStreaming(true);

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (event) => {
      receivedAnyRef.current = true;
      try {
        const parsed: SSEEvent = JSON.parse(event.data);
        const result = onEventRef.current(parsed);
        if (result === 'close') {
          es.close();
          esRef.current = null;
          setIsStreaming(false);
        }
      } catch (e) {
        console.error('[useSSE] Failed to parse event data', e);
      }
    };

    es.onerror = () => {
      // EventSource gives us neither a status code nor a body on error.
      // If we never received any events, it's almost certainly a 402 (insufficient Berrix).
      if (!receivedAnyRef.current) {
        setError(paymentErrorMessage);
        setErrorKind('payment');
      }
      es.close();
      esRef.current = null;
      setIsStreaming(false);
    };
  }, [url, requireAuth, authErrorMessage, paymentErrorMessage]);

  // Close the stream when the component unmounts.
  useEffect(() => {
    return () => {
      esRef.current?.close();
      esRef.current = null;
    };
  }, []);

  return { start, stop, isStreaming, error, errorKind };
}
