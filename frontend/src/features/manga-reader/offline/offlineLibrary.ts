import { createStore, set as idbSet, get as idbGet, del as idbDel } from 'idb-keyval';

const store = createStore('animetix-offline', 'kv');

export interface DownloadablePage {
  number: number;
  image_url: string;
}

export interface ChapterMeta {
  mediaId: string;
  mediaTitle: string;
  chapterNumber: number;
  chapterTitle: string;
}

export interface DownloadedChapter {
  mediaId: string;
  mediaTitle: string;
  chapterNumber: number;
  chapterTitle: string;
  pageCount: number;
  pageKeys: string[];
  downloadedAt: number;
  totalBytes: number;
}

export class OfflineQuotaError extends Error {
  constructor(message = 'Espace de stockage insuffisant pour ce chapitre.') {
    super(message);
    this.name = 'OfflineQuotaError';
  }
}

const INDEX_KEY = 'index';

const chapterId = (mediaId: string, chapterNumber: number) => `${mediaId}:${chapterNumber}`;
const metaKey = (mediaId: string, chapterNumber: number) => `meta:${chapterId(mediaId, chapterNumber)}`;
const pageKey = (mediaId: string, chapterNumber: number, pageNumber: number) =>
  `img:${chapterId(mediaId, chapterNumber)}:${pageNumber}`;

async function readIndex(): Promise<string[]> {
  return (await idbGet<string[]>(INDEX_KEY, store)) ?? [];
}

async function writeIndex(ids: string[]): Promise<void> {
  await idbSet(INDEX_KEY, ids, store);
}

function isQuotaError(err: unknown): boolean {
  return err instanceof Error && (err.name === 'QuotaExceededError' || err.name === 'OfflineQuotaError');
}

export async function isChapterDownloaded(mediaId: string, chapterNumber: number): Promise<boolean> {
  return (await readIndex()).includes(chapterId(mediaId, chapterNumber));
}

export async function getDownloadedChapter(
  mediaId: string,
  chapterNumber: number,
): Promise<DownloadedChapter | null> {
  return (await idbGet<DownloadedChapter>(metaKey(mediaId, chapterNumber), store)) ?? null;
}

// Internal storage format — ArrayBuffer survives structuredClone in all environments (jsdom, Node, browsers).
interface StoredPage { buffer: ArrayBuffer; type: string }

export async function getChapterPageBlobs(mediaId: string, chapterNumber: number): Promise<Blob[]> {
  const meta = await getDownloadedChapter(mediaId, chapterNumber);
  if (!meta) return [];
  const storedItems = await Promise.all(meta.pageKeys.map((k) => idbGet<StoredPage>(k, store)));
  return storedItems
    .filter((item): item is StoredPage => item != null && typeof item.type === 'string' && typeof item.buffer === 'object' && item.buffer !== null && typeof (item.buffer as ArrayBuffer).byteLength === 'number')
    .map((item) => new Blob([item.buffer], { type: item.type }));
}

export async function deleteChapter(mediaId: string, chapterNumber: number): Promise<void> {
  const meta = await getDownloadedChapter(mediaId, chapterNumber);
  if (meta) {
    await Promise.all(meta.pageKeys.map((k) => idbDel(k, store)));
  }
  await idbDel(metaKey(mediaId, chapterNumber), store);
  const id = chapterId(mediaId, chapterNumber);
  await writeIndex((await readIndex()).filter((x) => x !== id));
}

export async function listDownloads(): Promise<DownloadedChapter[]> {
  const ids = await readIndex();
  const metas = await Promise.all(
    ids.map((id) => {
      // chapterId is `${mediaId}:${chapterNumber}`; split on the LAST colon so
      // mediaIds that themselves contain a colon still parse correctly.
      const lastColon = id.lastIndexOf(':');
      const mediaId = id.slice(0, lastColon);
      const num = Number(id.slice(lastColon + 1));
      return getDownloadedChapter(mediaId, num);
    }),
  );
  return metas.filter((m): m is DownloadedChapter => m !== null);
}

export async function downloadChapter(
  meta: ChapterMeta,
  pages: DownloadablePage[],
  onProgress?: (ratio: number) => void,
): Promise<DownloadedChapter> {
  // Start clean so a previous partial/old copy never lingers.
  await deleteChapter(meta.mediaId, meta.chapterNumber);

  const ordered = [...pages].sort((a, b) => a.number - b.number);
  const writtenKeys: string[] = [];
  let totalBytes = 0;

  try {
    for (let i = 0; i < ordered.length; i++) {
      const page = ordered[i];
      const res = await fetch(page.image_url, { credentials: 'include' });
      if (!res.ok) throw new Error(`Échec du téléchargement de la page ${page.number} (${res.status})`);
      const blob = await res.blob();
      const buffer = await blob.arrayBuffer();
      const key = pageKey(meta.mediaId, meta.chapterNumber, page.number);
      await idbSet(key, { buffer, type: blob.type }, store);
      writtenKeys.push(key);
      totalBytes += blob.size;
      onProgress?.((i + 1) / ordered.length);
    }

    const record: DownloadedChapter = {
      mediaId: meta.mediaId,
      mediaTitle: meta.mediaTitle,
      chapterNumber: meta.chapterNumber,
      chapterTitle: meta.chapterTitle,
      pageCount: ordered.length,
      pageKeys: writtenKeys,
      downloadedAt: Date.now(),
      totalBytes,
    };
    await idbSet(metaKey(meta.mediaId, meta.chapterNumber), record, store);

    const id = chapterId(meta.mediaId, meta.chapterNumber);
    const index = await readIndex();
    if (!index.includes(id)) await writeIndex([...index, id]);

    return record;
  } catch (err) {
    // Roll back any partially written blobs; nothing should look "downloaded".
    await Promise.all(writtenKeys.map((k) => idbDel(k, store).catch(() => {})));
    if (isQuotaError(err)) throw new OfflineQuotaError();
    throw err;
  }
}
