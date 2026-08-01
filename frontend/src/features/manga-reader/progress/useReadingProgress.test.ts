import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import * as svc from './progressService';
import { useReaderStore } from '../stores/useReaderStore';
import { mangaFavoritesKey, mangaProgressKey } from './useMangaProgress';
import { useReadingProgress } from './useReadingProgress';

// `@testing-library`'s `waitFor` only auto-advances fake timers when it can
// detect them via a global `jest`, which plain vitest doesn't provide — left
// unshimmed, the "flushes on unmount" test below hangs until the outer
// runner timeout instead of resolving on the already-synchronous flush.
// Scoped to this file only; does not change what any assertion checks.
(globalThis as unknown as { jest?: typeof vi }).jest = vi;

// Un VRAI QueryClient (pas un mock de react-query) : l'invalidation est
// justement le comportement de cache que les tests précédents ne voyaient pas.
// Les deux clés sont pré-remplies pour pouvoir observer leur `isInvalidated`.
let queryClient: QueryClient;
const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(QueryClientProvider, { client: queryClient }, children);

const isInvalidated = (key: readonly unknown[]) =>
  queryClient.getQueryState(key)?.isInvalidated ?? false;

beforeEach(() => {
  vi.useFakeTimers();
  vi.restoreAllMocks();
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(mangaProgressKey('m1'), {
    chapters: [],
    resume: null,
    read_count: 0,
    total_count: 1,
  });
  queryClient.setQueryData(mangaFavoritesKey, []);
  useReaderStore.setState({
    pages: [
      { url: 'a', index: 0 },
      { url: 'b', index: 1 },
      { url: 'c', index: 2 },
    ],
    currentPageIndex: 0,
  });
});
afterEach(() => vi.useRealTimers());

describe('useReadingProgress', () => {
  it('debounces writes while pages are turned', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    renderHook(() => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }), {
      wrapper,
    });

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(1);
    });
    act(() => {
      useReaderStore.getState().setCurrentPageIndex(2);
    });
    expect(put).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(1500);
    });
    expect(put).toHaveBeenCalledTimes(1);
    expect(put).toHaveBeenCalledWith('m1', '1', { last_page_read: 2, is_read: true });
  });

  it('flushes the pending write on unmount', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    const { unmount } = renderHook(
      () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
      { wrapper },
    );

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(1);
    });
    unmount();

    await waitFor(() =>
      expect(put).toHaveBeenCalledWith('m1', '1', {
        last_page_read: 1,
        is_read: false,
      }),
    );
  });

  // Regression: opening a chapter used to be enough to write. The mount
  // effect armed `{last_page_read: 0, is_read: false}` — currentPageIndex is
  // 0 until the resume lands — and the debounce fired it 1.5 s later with no
  // user action at all, wiping a finished chapter back to unread/page 0.
  it('writes nothing on a passive mount, with no page turn', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    const { unmount } = renderHook(
      () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
      { wrapper },
    );

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    expect(put).not.toHaveBeenCalled();

    // Closing the tab during that window must not turn the mount into a write
    // either: the exit flush has nothing pending to send.
    unmount();
    await act(async () => {
      await Promise.resolve();
    });
    expect(put).not.toHaveBeenCalled();
  });

  it('marks the current chapter read on demand, keeping the page reached', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    const { result } = renderHook(
      () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
      { wrapper },
    );

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(1);
    });
    act(() => {
      result.current.markCurrentChapterRead();
    });

    // Immediate — no debounce window — and a single call: "next chapter" must
    // not double-notify the trackers.
    expect(put).toHaveBeenCalledTimes(1);
    expect(put).toHaveBeenCalledWith('m1', '1', { last_page_read: 1, is_read: true });

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });
    expect(put).toHaveBeenCalledTimes(1);
  });

  it('marks nothing when disabled (anonymous visitor)', () => {
    const put = vi.spyOn(svc, 'putChapterProgress');
    const { result } = renderHook(
      () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: false }),
      { wrapper },
    );

    act(() => {
      result.current.markCurrentChapterRead();
    });

    expect(put).not.toHaveBeenCalled();
  });

  it('writes nothing at all when disabled', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress');
    renderHook(() => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: false }), {
      wrapper,
    });

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(2);
    });
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    expect(put).not.toHaveBeenCalled();
  });

  // Le défaut : la spec exige que /progress/ soit « invalidée après chaque
  // écriture », et le lecteur n'invalidait rien. Comme tout le cache est
  // persisté 24 h en IndexedDB (utils/queryClient), la fiche œuvre, la popup
  // Tachidesk et la bibliothèque continuaient d'afficher l'état d'avant.
  //
  // Ces tests observent un VRAI QueryClient : c'est `isInvalidated` sur les
  // deux clés réellement utilisées par ces écrans qui est vérifié, pas un
  // espion posé sur `invalidateQueries`.
  describe('cache invalidation', () => {
    it('leaves the cache alone on an intermediate page turn', async () => {
      const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
      renderHook(() => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }), {
        wrapper,
      });

      // Page 2/3 : on lit, on n'a pas fini le chapitre.
      act(() => {
        useReaderStore.getState().setCurrentPageIndex(1);
      });
      await act(async () => {
        vi.advanceTimersByTime(1500);
        await Promise.resolve();
      });

      expect(put).toHaveBeenCalledWith('m1', '1', { last_page_read: 1, is_read: false });
      // Une relecture ici partirait toutes les 1,5 s pendant toute la lecture.
      expect(isInvalidated(mangaProgressKey('m1'))).toBe(false);
      expect(isInvalidated(mangaFavoritesKey)).toBe(false);
    });

    it('invalidates both keys when the chapter flips to read', async () => {
      vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
      renderHook(() => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }), {
        wrapper,
      });

      // Dernière page : is_read passe à true — les pastilles, le bandeau de
      // reprise et les compteurs de la bibliothèque changent tous.
      act(() => {
        useReaderStore.getState().setCurrentPageIndex(2);
      });
      await act(async () => {
        vi.advanceTimersByTime(1500);
        await Promise.resolve();
      });

      await waitFor(() => expect(isInvalidated(mangaProgressKey('m1'))).toBe(true));
      expect(isInvalidated(mangaFavoritesKey)).toBe(true);
    });

    // Le cas courant, et celui qu'une première version du correctif ratait :
    // pendant la lecture le debounce a DÉJÀ envoyé l'écriture, donc au moment
    // de quitter il n'y a plus rien en attente. Sans relecture ici, la fiche
    // œuvre et la bibliothèque repartaient sur la copie persistée.
    it('invalidates on exit even when the debounced write already went out', async () => {
      const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
      const { unmount } = renderHook(
        () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
        { wrapper },
      );

      act(() => {
        useReaderStore.getState().setCurrentPageIndex(1);
      });
      await act(async () => {
        vi.advanceTimersByTime(1500);
        await Promise.resolve();
      });
      expect(put).toHaveBeenCalledTimes(1);
      expect(isInvalidated(mangaProgressKey('m1'))).toBe(false);

      unmount();

      await waitFor(() => expect(isInvalidated(mangaProgressKey('m1'))).toBe(true));
      expect(isInvalidated(mangaFavoritesKey)).toBe(true);
      // Et surtout : pas de deuxième écriture au passage.
      expect(put).toHaveBeenCalledTimes(1);
    });

    it('invalidates both keys when leaving the reader mid-chapter', async () => {
      vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
      const { unmount } = renderHook(
        () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
        { wrapper },
      );

      act(() => {
        useReaderStore.getState().setCurrentPageIndex(1);
      });
      // Sortie avant la fin du debounce : le flush de sortie écrit ET relit.
      unmount();

      await waitFor(() => expect(isInvalidated(mangaProgressKey('m1'))).toBe(true));
      expect(isInvalidated(mangaFavoritesKey)).toBe(true);
    });

    it('invalidates both keys on "next chapter"', async () => {
      vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
      const { result } = renderHook(
        () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
        { wrapper },
      );

      act(() => {
        useReaderStore.getState().setCurrentPageIndex(1);
      });
      act(() => {
        result.current.markCurrentChapterRead();
      });

      await waitFor(() => expect(isInvalidated(mangaProgressKey('m1'))).toBe(true));
      expect(isInvalidated(mangaFavoritesKey)).toBe(true);
    });

    it('invalidates nothing for an anonymous visitor', async () => {
      const put = vi.spyOn(svc, 'putChapterProgress');
      const { unmount } = renderHook(
        () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: false }),
        { wrapper },
      );

      act(() => {
        useReaderStore.getState().setCurrentPageIndex(2);
      });
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });
      unmount();
      await act(async () => {
        await Promise.resolve();
      });

      expect(put).not.toHaveBeenCalled();
      expect(isInvalidated(mangaProgressKey('m1'))).toBe(false);
      expect(isInvalidated(mangaFavoritesKey)).toBe(false);
    });

    it('does not invalidate when the write itself failed', async () => {
      vi.spyOn(svc, 'putChapterProgress').mockRejectedValue(new Error('boom'));
      const { result } = renderHook(
        () => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
        { wrapper },
      );

      act(() => {
        useReaderStore.getState().setCurrentPageIndex(1);
      });
      act(() => {
        result.current.markCurrentChapterRead();
      });

      await waitFor(() => expect(result.current.saveState).toBe('error'));
      expect(isInvalidated(mangaProgressKey('m1'))).toBe(false);
      expect(isInvalidated(mangaFavoritesKey)).toBe(false);
    });
  });
});
