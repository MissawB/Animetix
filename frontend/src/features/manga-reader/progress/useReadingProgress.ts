import { useCallback, useEffect, useRef, useState } from 'react';
import { useReaderStore } from '../stores/useReaderStore';
import { putChapterProgress } from './progressService';

const DEBOUNCE_MS = 1500;

export type SaveState = 'idle' | 'saving' | 'saved' | 'error';

interface Options {
  mediaId: string | undefined;
  chapterNumber: string | undefined;
  enabled: boolean;
}

interface PendingWrite {
  mediaId: string;
  chapterNumber: string;
  last_page_read: number;
  is_read: boolean;
}

/** Écrit la progression pendant la lecture. Debouncé, avec flush garanti à la
 *  sortie : sans ça, fermer l'onglet perdrait la dernière page lue. */
export function useReadingProgress({ mediaId, chapterNumber, enabled }: Options) {
  const currentPageIndex = useReaderStore((s) => s.currentPageIndex);
  const pageCount = useReaderStore((s) => s.pages.length);
  const [saveState, setSaveState] = useState<SaveState>('idle');

  // The chapter identity travels with the pending write itself, so `flush`
  // never needs to read props/state that could be stale by the time it runs.
  const pending = useRef<PendingWrite | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Stable across renders (empty deps): it only ever reads ref.current at
  // call time, so re-defining it per render would gain nothing but would
  // force the effects below to resubscribe/reschedule needlessly.
  const flush = useCallback(() => {
    const payload = pending.current;
    if (!payload) return;
    pending.current = null;
    const { mediaId: id, chapterNumber: chapter, ...body } = payload;
    setSaveState('saving');
    putChapterProgress(id, chapter, body)
      .then(() => setSaveState('saved'))
      .catch(() => setSaveState('error'));
  }, []);

  // Debounces the write while pages are turned: only records the *latest*
  // page and (re)schedules the timer. Cleanup only clears the timeout — it
  // must NOT flush here, since this effect reruns on every page change and
  // an unconditional flush-on-cleanup would defeat the debounce entirely.
  useEffect(() => {
    if (!enabled || !mediaId || !chapterNumber || pageCount === 0) return;

    pending.current = {
      mediaId,
      chapterNumber,
      last_page_read: currentPageIndex,
      is_read: currentPageIndex >= pageCount - 1,
    };

    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(flush, DEBOUNCE_MS);

    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [enabled, mediaId, chapterNumber, currentPageIndex, pageCount, flush]);

  // Flushes on tab hide / real unmount. Deliberately scoped to
  // [enabled, mediaId, chapterNumber] only (not currentPageIndex) so the
  // listeners — and the flush-on-cleanup — persist across page turns and
  // only fire on an actual exit or chapter change. Without this split,
  // closing the tab would lose the last page read.
  useEffect(() => {
    if (!enabled || !mediaId || !chapterNumber) return;

    const onHide = () => {
      if (document.visibilityState === 'hidden') flush();
    };
    window.addEventListener('pagehide', flush);
    document.addEventListener('visibilitychange', onHide);

    return () => {
      window.removeEventListener('pagehide', flush);
      document.removeEventListener('visibilitychange', onHide);
      flush();
    };
  }, [enabled, mediaId, chapterNumber, flush]);

  return { saveState };
}
