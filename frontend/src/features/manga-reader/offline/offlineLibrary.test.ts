import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  downloadChapter,
  isChapterDownloaded,
  getChapterPageBlobs,
  getDownloadedChapter,
  deleteChapter,
  listDownloads,
  OfflineQuotaError,
} from './offlineLibrary';

const META = { mediaId: 'm1', mediaTitle: 'Test Manga', chapterNumber: 3, chapterTitle: 'Ch 3' };
const PAGES = [
  { number: 0, image_url: 'https://host/p0.jpg' },
  { number: 1, image_url: 'https://host/p1.jpg' },
];

function mockFetchOk() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => ({
      ok: true,
      blob: async () => new Blob([url], { type: 'image/jpeg' }),
    })),
  );
}

describe('offlineLibrary', () => {
  beforeEach(async () => {
    // Clear DB between tests by deleting any known chapter
    await deleteChapter('m1', 3).catch(() => {});
  });
  afterEach(() => vi.unstubAllGlobals());

  it('downloads, stores blobs + meta, and reports progress', async () => {
    mockFetchOk();
    const progress: number[] = [];
    const result = await downloadChapter(META, PAGES, (r) => progress.push(r));

    expect(result.pageCount).toBe(2);
    expect(result.pageKeys).toHaveLength(2);
    expect(await isChapterDownloaded('m1', 3)).toBe(true);
    expect(progress[progress.length - 1]).toBe(1);

    const blobs = await getChapterPageBlobs('m1', 3);
    expect(blobs).toHaveLength(2);
    expect(await blobs[0].text()).toBe('https://host/p0.jpg'); // ordered by page number
  });

  it('is idempotent: re-downloading overwrites cleanly', async () => {
    mockFetchOk();
    await downloadChapter(META, PAGES);
    await downloadChapter(META, PAGES);
    expect((await getChapterPageBlobs('m1', 3))).toHaveLength(2);
    expect(await listDownloads()).toHaveLength(1);
  });

  it('deleteChapter removes blobs, meta, and index entry', async () => {
    mockFetchOk();
    await downloadChapter(META, PAGES);
    await deleteChapter('m1', 3);
    expect(await isChapterDownloaded('m1', 3)).toBe(false);
    expect(await getDownloadedChapter('m1', 3)).toBeNull();
    expect(await getChapterPageBlobs('m1', 3)).toHaveLength(0);
    expect(await listDownloads()).toHaveLength(0);
  });

  it('rolls back and rejects when a page fetch fails (nothing left downloaded)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (url.endsWith('p1.jpg')) return { ok: false, status: 500, blob: async () => new Blob() };
        return { ok: true, blob: async () => new Blob([url]) };
      }),
    );
    await expect(downloadChapter(META, PAGES)).rejects.toThrow();
    expect(await isChapterDownloaded('m1', 3)).toBe(false);
    expect(await getChapterPageBlobs('m1', 3)).toHaveLength(0);
  });

  it('wraps QuotaExceededError as OfflineQuotaError', async () => {
    mockFetchOk();
    // Force the second blob store to throw a quota error by spying via a sabotaged fetch blob
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        blob: async () => {
          const e = new Error('quota');
          e.name = 'QuotaExceededError';
          throw e;
        },
      })),
    );
    await expect(downloadChapter(META, PAGES)).rejects.toBeInstanceOf(OfflineQuotaError);
    expect(await isChapterDownloaded('m1', 3)).toBe(false);
  });
});
