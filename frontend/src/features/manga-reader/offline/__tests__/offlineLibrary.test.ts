import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { clear, createStore } from 'idb-keyval';
import {
  downloadChapter,
  deleteChapter,
  getDownloadedChapter,
  getChapterPageBlobs,
  isChapterDownloaded,
  listDownloads,
  OfflineQuotaError,
  type ChapterMeta,
  type DownloadablePage,
} from '../offlineLibrary';

// Must match the store name/version used inside offlineLibrary.ts so beforeEach
// can wipe the exact same object store the module writes to.
const store = createStore('animetix-offline', 'kv');

const META: ChapterMeta = {
  mediaId: 'manga-1',
  mediaTitle: 'Test Manga',
  chapterNumber: 12,
  chapterTitle: 'The Test Chapter',
};

const PAGES: DownloadablePage[] = [
  { number: 2, image_url: 'https://example.com/p2.png' },
  { number: 1, image_url: 'https://example.com/p1.png' },
];

// Map each page URL to deterministic bytes so we can assert real round-trips.
const PAGE_BYTES: Record<string, number[]> = {
  'https://example.com/p1.png': [137, 80, 78, 71], // PNG-ish header
  'https://example.com/p2.png': [1, 2, 3, 4, 5, 6],
};

function mockFetchWithImages() {
  global.fetch = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    const bytes = PAGE_BYTES[url];
    if (!bytes) {
      return { ok: false, status: 404 } as Response;
    }
    const blob = new Blob([new Uint8Array(bytes)], { type: 'image/png' });
    return {
      ok: true,
      status: 200,
      blob: async () => blob,
    } as unknown as Response;
  }) as typeof fetch;
}

async function blobBytes(blob: Blob): Promise<number[]> {
  return Array.from(new Uint8Array(await blob.arrayBuffer()));
}

describe('offlineLibrary', () => {
  beforeEach(async () => {
    await clear(store);
    mockFetchWithImages();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns empty results when nothing is downloaded', async () => {
    expect(await listDownloads()).toEqual([]);
    expect(await isChapterDownloaded('manga-1', 12)).toBe(false);
    expect(await getDownloadedChapter('manga-1', 12)).toBeNull();
    expect(await getChapterPageBlobs('manga-1', 12)).toEqual([]);
  });

  it('downloads a chapter and returns a record with sorted pages and totals', async () => {
    const record = await downloadChapter(META, PAGES);

    expect(record.mediaId).toBe('manga-1');
    expect(record.mediaTitle).toBe('Test Manga');
    expect(record.chapterNumber).toBe(12);
    expect(record.chapterTitle).toBe('The Test Chapter');
    expect(record.pageCount).toBe(2);
    // PAGES given out of order (2 then 1) -> keys stored sorted by page number.
    expect(record.pageKeys).toEqual([
      'img:manga-1:12:1',
      'img:manga-1:12:2',
    ]);
    // 4 bytes (p1) + 6 bytes (p2) = 10.
    expect(record.totalBytes).toBe(10);
    expect(typeof record.downloadedAt).toBe('number');
  });

  it('marks the chapter as downloaded and lists it back', async () => {
    await downloadChapter(META, PAGES);

    expect(await isChapterDownloaded('manga-1', 12)).toBe(true);

    const list = await listDownloads();
    expect(list).toHaveLength(1);
    expect(list[0].mediaId).toBe('manga-1');
    expect(list[0].chapterNumber).toBe(12);
    expect(list[0].pageCount).toBe(2);
  });

  it('round-trips the stored meta record via getDownloadedChapter', async () => {
    const record = await downloadChapter(META, PAGES);
    const fetched = await getDownloadedChapter('manga-1', 12);
    expect(fetched).toEqual(record);
  });

  it('round-trips the actual page image bytes via getChapterPageBlobs', async () => {
    await downloadChapter(META, PAGES);

    const blobs = await getChapterPageBlobs('manga-1', 12);
    expect(blobs).toHaveLength(2);
    expect(blobs[0].type).toBe('image/png');
    // Blobs come back in pageKeys order (page 1 then page 2).
    expect(await blobBytes(blobs[0])).toEqual([137, 80, 78, 71]);
    expect(await blobBytes(blobs[1])).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it('deletes a chapter, its pages, and removes it from the index', async () => {
    await downloadChapter(META, PAGES);
    expect(await isChapterDownloaded('manga-1', 12)).toBe(true);

    await deleteChapter('manga-1', 12);

    expect(await isChapterDownloaded('manga-1', 12)).toBe(false);
    expect(await getDownloadedChapter('manga-1', 12)).toBeNull();
    expect(await getChapterPageBlobs('manga-1', 12)).toEqual([]);
    expect(await listDownloads()).toEqual([]);
  });

  it('deleting a non-existent chapter is a no-op and does not throw', async () => {
    await expect(deleteChapter('nope', 99)).resolves.toBeUndefined();
    expect(await listDownloads()).toEqual([]);
  });

  it('re-downloading replaces the prior copy without duplicating the index entry', async () => {
    await downloadChapter(META, PAGES);
    await downloadChapter(META, [PAGES[1]]); // only page 1 this time

    const list = await listDownloads();
    expect(list).toHaveLength(1);
    expect(list[0].pageCount).toBe(1);
    expect(list[0].pageKeys).toEqual(['img:manga-1:12:1']);
  });

  it('handles mediaIds that themselves contain a colon when listing', async () => {
    const weird: ChapterMeta = { ...META, mediaId: 'series:arc:7' };
    await downloadChapter(weird, [PAGES[1]]);

    const list = await listDownloads();
    expect(list).toHaveLength(1);
    expect(list[0].mediaId).toBe('series:arc:7');
    expect(list[0].chapterNumber).toBe(12);
  });

  it('keeps multiple chapters independent', async () => {
    await downloadChapter(META, PAGES);
    await downloadChapter({ ...META, chapterNumber: 13, chapterTitle: 'Next' }, [PAGES[1]]);

    const list = await listDownloads();
    expect(list).toHaveLength(2);
    expect(list.map((c) => c.chapterNumber).sort()).toEqual([12, 13]);
  });

  it('rolls back and surfaces a fetch failure without leaving a downloaded chapter', async () => {
    const badPages: DownloadablePage[] = [
      { number: 1, image_url: 'https://example.com/p1.png' },
      { number: 2, image_url: 'https://example.com/missing.png' }, // 404
    ];

    await expect(downloadChapter(META, badPages)).rejects.toThrow();

    expect(await isChapterDownloaded('manga-1', 12)).toBe(false);
    expect(await getDownloadedChapter('manga-1', 12)).toBeNull();
    // Partially-written page blobs must have been rolled back.
    expect(await getChapterPageBlobs('manga-1', 12)).toEqual([]);
  });

  it('maps a QuotaExceededError during write to OfflineQuotaError', async () => {
    // First page fetch succeeds, but the blob.arrayBuffer throws a quota error,
    // mimicking IndexedDB rejecting the write under storage pressure.
    global.fetch = vi.fn(async () => {
      const quota = new Error('quota');
      quota.name = 'QuotaExceededError';
      return {
        ok: true,
        status: 200,
        blob: async () => ({
          type: 'image/png',
          size: 1,
          arrayBuffer: async () => {
            throw quota;
          },
        }),
      } as unknown as Response;
    }) as typeof fetch;

    await expect(
      downloadChapter(META, [{ number: 1, image_url: 'https://example.com/p1.png' }]),
    ).rejects.toBeInstanceOf(OfflineQuotaError);

    expect(await isChapterDownloaded('manga-1', 12)).toBe(false);
  });
});
