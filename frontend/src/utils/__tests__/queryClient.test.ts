import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as Sentry from '@sentry/react';

// `persistQueryClient` runs at module import and would hit IndexedDB; stub it
// and the persister so importing `queryClient` is side-effect free.
vi.mock('@tanstack/react-query-persist-client', () => ({
  persistQueryClient: vi.fn(),
}));
vi.mock('../persister', () => ({
  createPersister: vi.fn(() => ({
    persistClient: vi.fn(),
    restoreClient: vi.fn(),
    removeClient: vi.fn(),
  })),
}));
vi.mock('@sentry/react', () => ({
  captureException: vi.fn(),
}));

// Re-import fresh so module-level singletons are rebuilt under the mocks.
const importQueryClient = async () => {
  vi.resetModules();
  return await import('../queryClient');
};

type RetryFn = (failureCount: number, error: unknown) => boolean;

describe('queryClient retry policy', () => {
  let retry: RetryFn;

  beforeEach(async () => {
    const { queryClient } = await importQueryClient();
    retry = queryClient.getDefaultOptions().queries?.retry as RetryFn;
  });

  it('exposes a function as the default query retry option', () => {
    expect(typeof retry).toBe('function');
  });

  it('does not retry on 4xx client errors', () => {
    expect(retry(0, { status: 400 })).toBe(false);
    expect(retry(0, { status: 401 })).toBe(false);
    expect(retry(0, { status: 404 })).toBe(false);
    expect(retry(1, { status: 499 })).toBe(false);
  });

  it('retries up to 2 times on 5xx server errors', () => {
    expect(retry(0, { status: 500 })).toBe(true);
    expect(retry(1, { status: 503 })).toBe(true);
    // failureCount has reached the cap (2) -> stop retrying.
    expect(retry(2, { status: 500 })).toBe(false);
    expect(retry(3, { status: 500 })).toBe(false);
  });

  it('retries on network errors with no status attached', () => {
    expect(retry(0, new Error('Network down'))).toBe(true);
    expect(retry(1, null)).toBe(true);
    expect(retry(2, undefined)).toBe(false);
  });

  it('treats a non-numeric status as retryable', () => {
    expect(retry(0, { status: 'oops' as unknown as number })).toBe(true);
  });
});

describe('queryClient error reporting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('reports query cache errors to Sentry tagged as react-query:query', async () => {
    const { queryClient } = await importQueryClient();
    const cache = queryClient.getQueryCache();
    const error = new Error('query boom');

    cache.config.onError?.(
      error,
      // The query argument is unused by the handler.
      {} as Parameters<NonNullable<typeof cache.config.onError>>[1],
    );

    expect(Sentry.captureException).toHaveBeenCalledWith(error, {
      tags: { source: 'react-query:query' },
    });
  });

  it('reports mutation cache errors to Sentry tagged as react-query:mutation', async () => {
    const { queryClient } = await importQueryClient();
    const cache = queryClient.getMutationCache();
    const error = new Error('mutation boom');
    const onError = cache.config.onError as
      | ((...args: unknown[]) => void)
      | undefined;

    onError?.(error, undefined, undefined, {});

    expect(Sentry.captureException).toHaveBeenCalledWith(error, {
      tags: { source: 'react-query:mutation' },
    });
  });
});
