import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider, hydrate } from '@tanstack/react-query';
import React from 'react';
import * as apiMod from '../../../utils/apiClient';
import { mangaProgressKey } from './useMangaProgress';
import { useResumeReadingPosition } from './useResumeReadingPosition';

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client }, children);
};

/** Reproduit ce que `persistQueryClient` restaure depuis IndexedDB : un état
 *  de query complet, `status: 'success'`, horodaté d'une session précédente
 *  (le cache de l'app est conservé 24 h — voir utils/queryClient.ts). */
const persistedProgress = (mediaId: string, lastPageRead: number, ageMs: number) => {
  const dataUpdatedAt = Date.now() - ageMs;
  return {
    mutations: [],
    queries: [
      {
        dehydratedAt: dataUpdatedAt,
        queryKey: mangaProgressKey(mediaId),
        queryHash: JSON.stringify(mangaProgressKey(mediaId)),
        state: {
          data: {
            chapters: [{ number: 5, is_read: false, last_page_read: lastPageRead, page_count: 50 }],
            resume: { chapter_number: 5, last_page_read: lastPageRead },
            read_count: 0,
            total_count: 1,
          },
          dataUpdateCount: 1,
          dataUpdatedAt,
          error: null,
          errorUpdateCount: 0,
          errorUpdatedAt: 0,
          fetchFailureCount: 0,
          fetchFailureReason: null,
          fetchMeta: null,
          isInvalidated: false,
          status: 'success' as const,
          fetchStatus: 'idle' as const,
        },
      },
    ],
  };
};

beforeEach(() => vi.restoreAllMocks());

describe('useResumeReadingPosition', () => {
  // Regression: Suwayomi (chapter pages) can resolve before Django
  // (/progress/). If the once-per-chapter guard is consumed the moment
  // pages are ready — instead of waiting for the progress query to settle —
  // the resume is silently skipped forever once the saved position finally
  // arrives: the reader would restart at page 1 even though the user had
  // stopped at page 40.
  it('still resumes once the progress query settles, even when pages were ready first', async () => {
    let resolveApi: (value: unknown) => void = () => {};
    const pending = new Promise((resolve) => {
      resolveApi = resolve;
    });
    vi.spyOn(apiMod, 'apiClient').mockReturnValue(pending as Promise<unknown>);

    const setCurrentPageIndex = vi.fn();

    renderHook(
      () =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: true,
          isAuthLoading: false,
          readerPagesLength: 50, // pages already loaded
          setCurrentPageIndex,
        }),
      { wrapper },
    );

    // Progress request still in flight: nothing to resume from yet.
    expect(setCurrentPageIndex).not.toHaveBeenCalled();

    await act(async () => {
      resolveApi({
        chapters: [{ number: 5, is_read: false, last_page_read: 39, page_count: 50 }],
        resume: { chapter_number: 5, last_page_read: 39 },
        read_count: 0,
        total_count: 1,
      });
      await pending;
    });

    await waitFor(() => expect(setCurrentPageIndex).toHaveBeenCalledWith(39));
  });

  // `isResolved` is what gates the *writer* hook (useReadingProgress): while
  // it is false, currentPageIndex is a placeholder 0 rather than the reader's
  // real position, and writing it would erase the progress being restored.
  it('reports isResolved only once the resume question is settled', async () => {
    let resolveApi: (value: unknown) => void = () => {};
    const pending = new Promise((resolve) => {
      resolveApi = resolve;
    });
    vi.spyOn(apiMod, 'apiClient').mockReturnValue(pending as Promise<unknown>);

    const { result, rerender } = renderHook(
      (props: { readerPagesLength: number }) =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: true,
          isAuthLoading: false,
          readerPagesLength: props.readerPagesLength,
          setCurrentPageIndex: vi.fn(),
        }),
      { wrapper, initialProps: { readerPagesLength: 0 } },
    );

    // No pages yet, and no progress yet.
    expect(result.current.isResolved).toBe(false);

    rerender({ readerPagesLength: 50 });
    // Pages ready but /progress/ still in flight: still unresolved.
    expect(result.current.isResolved).toBe(false);

    await act(async () => {
      resolveApi({
        chapters: [{ number: 5, is_read: true, last_page_read: 82, page_count: 83 }],
        resume: null,
        read_count: 1,
        total_count: 1,
      });
      await pending;
    });

    await waitFor(() => expect(result.current.isResolved).toBe(true));
  });

  // Guards the new "wait for isFetched" branch: for an anonymous visitor
  // useMangaProgress never runs its query (enabled=false), so isFetched
  // would never become true — the hook must not wait on it forever.
  it('does not wait on the progress query for an anonymous visitor', async () => {
    const api = vi.spyOn(apiMod, 'apiClient');
    const setCurrentPageIndex = vi.fn();

    renderHook(
      () =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: false,
          isAuthLoading: false,
          readerPagesLength: 50,
          setCurrentPageIndex,
        }),
      { wrapper },
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(api).not.toHaveBeenCalled();
    expect(setCurrentPageIndex).not.toHaveBeenCalled();
  });

  // Regression: a deep-link render (favorite, F5, shared link) mounts before
  // Firebase's onAuthStateChanged/getRedirectResult has resolved. authStore
  // starts as { isAuthenticated: false, isLoading: true } on every app load
  // (see store/authStore.ts), so a naive `isAuthenticated && !progressFetched`
  // gate reads "anonymous, nothing to wait for" and consumes the guard on
  // the spot — then the effect exits on resumedRef alone once auth actually
  // resolves to logged-in, and the real saved position never gets applied.
  it('still resumes once auth resolves to logged-in, even if it read as anonymous at first render', async () => {
    vi.spyOn(apiMod, 'apiClient').mockResolvedValue({
      chapters: [{ number: 5, is_read: false, last_page_read: 39, page_count: 50 }],
      resume: { chapter_number: 5, last_page_read: 39 },
      read_count: 0,
      total_count: 1,
    });

    const setCurrentPageIndex = vi.fn();

    const { rerender } = renderHook(
      (props: { isAuthenticated: boolean; isAuthLoading: boolean }) =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: props.isAuthenticated,
          isAuthLoading: props.isAuthLoading,
          readerPagesLength: 50, // pages already loaded
          setCurrentPageIndex,
        }),
      { wrapper, initialProps: { isAuthenticated: false, isAuthLoading: true } },
    );

    // Auth not resolved yet: must not treat this as "anonymous, nothing to
    // resume" and burn the guard.
    expect(setCurrentPageIndex).not.toHaveBeenCalled();

    await act(async () => {
      rerender({ isAuthenticated: true, isAuthLoading: false });
      await Promise.resolve();
    });

    await waitFor(() => expect(setCurrentPageIndex).toHaveBeenCalledWith(39));
  });

  // Le défaut réel, celui que ni les tests qui mockent useMangaProgress ni ceux
  // qui partent d'un cache vide ne pouvaient voir : `utils/queryClient.ts`
  // persiste TOUT le cache 24 h en IndexedDB. Au montage suivant, la query
  // /progress/ est donc restaurée en `status: 'success'` — `isFetched` est
  // vrai dès le premier rendu, avec la position d'une session précédente.
  // La garde une-fois-par-chapitre se consommait là-dessus, et la vraie
  // réponse du serveur (arrivée 200 ms plus tard) ne servait plus à rien.
  //
  // Ce test utilise un vrai QueryClient + `hydrate()` : c'est le comportement
  // de cache lui-même qui est exercé, pas un mock du hook.
  it('ignores the persisted position and resumes where the server says', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    // Session précédente : le lecteur s'était arrêté page 41 (index 40).
    hydrate(client, persistedProgress('m1', 40, 6 * 60 * 60 * 1000));

    let resolveApi: (value: unknown) => void = () => {};
    const pending = new Promise((resolve) => {
      resolveApi = resolve;
    });
    const api = vi.spyOn(apiMod, 'apiClient').mockReturnValue(pending as Promise<unknown>);

    const setCurrentPageIndex = vi.fn();
    const persistedWrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client }, children);

    renderHook(
      () =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: true,
          isAuthLoading: false,
          readerPagesLength: 50,
          setCurrentPageIndex,
        }),
      { wrapper: persistedWrapper },
    );

    // La revalidation doit bien partir…
    await waitFor(() => expect(api).toHaveBeenCalledTimes(1));
    // …et surtout : rien n'est repris tant qu'elle n'a pas répondu. Sans le
    // correctif, la garde est consommée ici avec la position persistée (40).
    expect(setCurrentPageIndex).not.toHaveBeenCalled();

    await act(async () => {
      // Depuis, l'utilisateur a lu ailleurs : le serveur fait autorité.
      resolveApi({
        chapters: [{ number: 5, is_read: false, last_page_read: 3, page_count: 50 }],
        resume: { chapter_number: 5, last_page_read: 3 },
        read_count: 0,
        total_count: 1,
      });
      await pending;
    });

    await waitFor(() => expect(setCurrentPageIndex).toHaveBeenCalledWith(3));
    expect(setCurrentPageIndex).not.toHaveBeenCalledWith(40);
  });

  // Corollaire du test précédent : si la revalidation échoue (hors-ligne),
  // la reprise doit quand même se trancher, sinon `isResolved` reste faux
  // pour toujours et le lecteur n'écrit plus jamais la progression.
  it('settles even when the revalidation fails', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    hydrate(client, persistedProgress('m1', 40, 6 * 60 * 60 * 1000));
    vi.spyOn(apiMod, 'apiClient').mockRejectedValue(new Error('offline'));

    const persistedWrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client }, children);

    const { result } = renderHook(
      () =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: true,
          isAuthLoading: false,
          readerPagesLength: 50,
          setCurrentPageIndex: vi.fn(),
        }),
      { wrapper: persistedWrapper },
    );

    await waitFor(() => expect(result.current.isResolved).toBe(true));
  });
});
